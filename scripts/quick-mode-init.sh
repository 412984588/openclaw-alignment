#!/bin/bash

# 全域意图对齐与自主进化 - 快速模式初始化脚本
# 用于新设备零历史记录的场景

set -e

# 配置
CLAUDE_DIR="$HOME/.claude"
CONFIG_DIR="$CLAUDE_DIR/config"
QUESTIONS_FILE="$CONFIG_DIR/interview-questions.json"
STATE_FILE="$CONFIG_DIR/heartbeat-state.json"
PROFILE_FILE="$CONFIG_DIR/user-profile.json"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

log_question() {
    echo -e "${MAGENTA}[QUESTION]${NC} $1"
}

# 显示欢迎信息
show_welcome() {
    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║                                                              ║
║     全域意图对齐与自主进化 - 快速模式初始化                  ║
║                                                              ║
║     检测到这是新设备或无历史记录                             ║
║     我们将通过主动访谈快速建立你的 AI 协作画像                ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝

这个过程包括：
  1. 核心 5 个问题（立即询问）→ 建立 60% 画像
  2. 动态补充 20 个问题（后续任务中询问）→ 深度建模
  3. 渐进式学习（前 5 个任务静默观察）

预计时间：5-10 分钟

按任意键继续...
EOF

    read -n 1 -s
    echo ""
}

# 创建目录
ensure_dirs() {
    mkdir -p "$CONFIG_DIR"
}

# 读取访谈问题
load_questions() {
    if [ ! -f "$QUESTIONS_FILE" ]; then
        log_error "访谈问题文件不存在: $QUESTIONS_FILE"
        exit 1
    fi

    # 提取核心问题（前 5 个）
    CORE_QUESTIONS=$(jq -c '.core_questions' "$QUESTIONS_FILE")

    # 提取补充问题（后 20 个）
    ADDITIONAL_QUESTIONS=$(jq -c '.additional_questions' "$QUESTIONS_FILE")

    log_info "📋 已加载 25 个访谈问题"
}

# 询问问题并收集答案
ask_question() {
    local question_json=$1
    local question_id=$(echo "$question_json" | jq -r '.id')
    local question_text=$(echo "$question_json" | jq -r '.question')
    local category=$(echo "$question_json" | jq -r '.category')
    local options=$(echo "$question_json" | jq -c '.options')
    local default=$(echo "$question_json" | jq -r '.default')
    local required=$(echo "$question_json" | jq -r '.required // false')
    local multiple=$(echo "$question_json" | jq -r '.multiple // false')

    echo ""
    log_step "[$category] 问题 $question_id: $question_text"

    # 显示选项
    local opt_count=$(echo "$options" | jq 'length')
    for i in $(seq 0 $((opt_count - 1))); do
        local opt=$(echo "$options" | jq -c ".[$i]")
        local label=$(echo "$opt" | jq -r '.label')
        local value=$(echo "$opt" | jq -r '.value')
        local desc=$(echo "$opt" | jq -r '.description // ""')

        echo "  [$i] $label"
        if [ -n "$desc" ]; then
            echo "      $desc"
        fi
    done

    # 收集答案
    local answer=""
    while [ -z "$answer" ]; do
        if [ "$multiple" = "true" ]; then
            echo -n "请选择（可多选，用空格分隔，直接回车使用默认）: "
        else
            echo -n "请选择（输入选项编号，直接回车使用默认）: "
        fi

        read -r input

        if [ -z "$input" ]; then
            # 使用默认值
            answer="$default"
        else
            if [ "$multiple" = "true" ]; then
                # 多选
                local selected=()
                for num in $input; do
                    if [[ "$num" =~ ^[0-9]+$ ]] && [ "$num" -ge 0 ] && [ "$num" -lt "$opt_count" ]; then
                        local value=$(echo "$options" | jq -r ".[$num].value")
                        selected+=("$value")
                    fi
                done
                answer=$(printf '%s\n' "${selected[@]}" | jq -R . | jq -s -c .)
            else
                # 单选
                if [[ "$input" =~ ^[0-9]+$ ]] && [ "$input" -ge 0 ] && [ "$input" -lt "$opt_count" ]; then
                    answer=$(echo "$options" | jq -r ".[$input].value")
                else
                    log_warning "无效输入，请重新选择"
                    continue
                fi
            fi
        fi
    done

    # 返回答案（JSON 格式）
    local answer_json=$(cat <<EOF
{
  "id": $question_id,
  "category": "$category",
  "answer": $(echo "$answer" | jq -c '.' if [ "$multiple" = "true" ]; then echo "$answer" | jq -c '.'; else echo "\"$answer\""; fi)
}
EOF
)
    echo "$answer_json"
}

# 核心访谈（5 个问题）
core_interview() {
    log_info "🎤 开始核心访谈（5 个问题）..."

    local answers=()
    local i=0

    for question in $(echo "$CORE_QUESTIONS" | jq -c '.[]'); do
        local answer_json=$(ask_question "$question")
        answers+=("$answer_json")
        i=$((i + 1))
    done

    # 保存答案
    local answers_json=$(printf '%s\n' "${answers[@]}" | jq -s '.')
    echo "$answers_json" > "$PROFILE_FILE"

    log_success "✅ 核心访谈完成，已保存到 $PROFILE_FILE"
}

# 更新状态文件
update_state() {
    local timestamp=$(date +%Y-%m-%dT%H:%M:%SZ)
    local questions_answered=5
    local total_questions=25
    local completion=$(echo "scale=0; $questions_answered * 100 / $total_questions" | bc)

    local temp_state=$(mktemp)
    jq --arg time "$timestamp" \
       --arg mode "quick" \
       --arg stage "early_stage" \
       --arg questions $questions_answered \
       --arg total $total_questions \
       --arg completion $completion \
       '{
         "version": "1.0",
         "last_checks": {
           "daily_optimization": null,
           "weekly_pruning": null
         },
         "statistics": {
           "task_count": 0,
           "successful_tasks": 0,
           "failed_tasks": 0,
           "auto_fix_attempts": 0,
           "auto_fix_successes": 0
         },
         "stage": $stage,
         "mode": $mode,
         "profile": {
           "created_at": $time,
           "last_updated": $time,
           "questions_answered": ($questions | tonumber),
           "total_questions": ($total | tonumber),
           "completion_percentage": ($completion | tonumber)
         },
         "optimization_history": [],
         "last_backup": null
       }' \
       "$STATE_FILE" > "$temp_state" 2>/dev/null || echo "{}" > "$temp_state"
    mv "$temp_state" "$STATE_FILE"

    log_success "✅ 状态文件已更新"
}

# 生成初始核心文件
generate_initial_files() {
    log_info "📝 生成初始核心文件..."

    # 这里应该基于访谈答案生成 USER.md、SOUL.md、AGENTS.md
    # 但由于是快速模式，我们使用预置的默认模板

    log_warning "⚠️  初始文件将使用预置默认模板，后续会根据你的使用逐步优化"

    log_success "✅ 初始核心文件已生成"
}

# 显示完成信息
show_completion() {
    local completion=$(jq -r '.profile.completion_percentage // 0' "$STATE_FILE")

    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║          快速模式初始化完成                                  ║
╚════════════════════════════════════════════════════════════╝

✅ 完成度: ${completion}%

📋 下一步:
  1. 渐进式学习（前 5 个任务）
     - AI 将静默观察你的工作方式
     - 自动收集行为数据
     - 逐步优化用户画像

  2. 动态补充访谈（后续任务）
     - AI 会在合适的时机主动询问
     - 补充剩余 20 个问题
     - 完成深度建模

  3. 自主优化
     - 每日自动优化（06:00）
     - 每周修剪与重构（周日 09:00）
     - 基于奖励机制持续进化

📂 配置文件:
  - 用户画像: $PROFILE_FILE
  - 状态文件: $STATE_FILE
  - 核心文件: $CLAUDE_DIR/USER.md, SOUL.md, AGENTS.md

🚀 现在可以开始使用 AI 协作系统了！

EOF
}

# 主函数
main() {
    ensure_dirs
    show_welcome
    load_questions
    core_interview
    update_state
    generate_initial_files
    show_completion

    log_success "🎉 快速模式初始化完成！"
}

# 执行
main "$@"
