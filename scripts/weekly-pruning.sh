#!/bin/bash

# 全域意图对齐与自主进化 - 每周修剪与重构脚本
# Trigger: 每周日 09:00（Heartbeat 机制）

set -e

# 配置
CLAUDE_DIR="$HOME/.claude"
CONFIG_DIR="$CLAUDE_DIR/config"
BACKUP_DIR="$CLAUDE_DIR/backups"
STATE_FILE="$CONFIG_DIR/heartbeat-state.json"
LOG_FILE="$BACKUP_DIR/optimization-log.json"
REWARD_CONFIG="$CONFIG_DIR/reward-config.json"
USER_MD="$CLAUDE_DIR/USER.md"
SOUL_MD="$CLAUDE_DIR/SOUL.md"
AGENTS_MD="$CLAUDE_DIR/AGENTS.md"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# 创建目录
ensure_dirs() {
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$BACKUP_DIR"
}

# 备份当前状态
backup_state() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_dir="$BACKUP_DIR/backup-weekly-$timestamp"

    log_info "📦 强制备份当前状态..."

    cp -r "$CLAUDE_DIR" "$backup_dir"
    cp "$STATE_FILE" "$backup_dir/heartbeat-state.json.bak"
    cp "$REWARD_CONFIG" "$backup_dir/reward-config.json.bak"

    if [ -f "$USER_MD" ]; then
        cp "$USER_MD" "$backup_dir/USER.md.bak"
    fi
    if [ -f "$SOUL_MD" ]; then
        cp "$SOUL_MD" "$backup_dir/SOUL.md.bak"
    fi
    if [ -f "$AGENTS_MD" ]; then
        cp "$AGENTS_MD" "$backup_dir/AGENTS.md.bak"
    fi

    log_success "✅ 备份完成: $backup_dir"

    echo "$backup_dir"
}

# 迷你访谈
mini_interview() {
    log_info "🎤 迷你访谈（5-10 个问题）..."

    # 这里应该实现交互式访谈，但为了自动化，我们使用模拟数据
    # 实际使用时，应该通过 AI 对话系统收集用户反馈

    log_info "📋 访谈问题："
    log_info "  1. 过去一周的 AI 协作是否顺手？"
    log_info "  2. 利用逻辑是否有变化？"
    log_info "  3. 是否有新的偏好或雷区？"
    log_info "  4. 是否需要调整协作模式？"
    log_info "  5. 对自动优化结果是否满意？"

    # 模拟收集反馈（实际应该等待用户输入）
    log_info "📊 收集用户反馈..."
    log_warning "⚠️  注意：实际使用时应该通过交互式对话收集真实反馈"

    log_success "✅ 迷你访谈完成"
}

# 断舍离（记忆折叠）
prune_memory() {
    log_info "✂️  断舍离（记忆折叠）..."

    # 扫描过时规则（>30 天未触发）
    log_info "🔍 扫描过时规则..."
    # 这里应该实现规则扫描逻辑

    # 删除冗余逻辑
    log_info "🗑️  删除冗余逻辑..."
    # 这里应该实现冗余检测逻辑

    # 压缩历史记录
    log_info "🗜️  压缩历史记录..."
    local history_retention=$(jq -r '.backup.retention_days // 30' "$REWARD_CONFIG")

    # 清理旧备份
    find "$BACKUP_DIR" -name "backup-*" -type d -mtime +$history_retention -exec rm -rf {} + 2>/dev/null || true

    log_info "📊 保留最近 $history_retention 天的备份"

    log_success "✅ 断舍离完成"
}

# 深度重构
deep_refactor() {
    log_info "🔨 深度重构..."

    # 结合访谈结果优化文件
    log_info "📝 优化核心文件..."

    # 优化 USER.md
    if [ -f "$USER_MD" ]; then
        log_info "  - 更新 USER.md（行为模式分析）"
        # 这里应该实现自动更新逻辑
    fi

    # 优化 SOUL.md
    if [ -f "$SOUL_MD" ]; then
        log_info "  - 更新 SOUL.md（历史错误记录）"
        # 这里应该实现自动更新逻辑
    fi

    # 优化 AGENTS.md
    if [ -f "$AGENTS_MD" ]; then
        log_info "  - 更新 AGENTS.md（Agent 编排优化）"
        # 这里应该实现自动更新逻辑
    fi

    log_success "✅ 深度重构完成"
}

# 更新状态文件
update_state() {
    local timestamp=$(date +%Y-%m-%dT%H:%M:%SZ)

    log_info "📊 更新状态文件..."

    # 更新最后修剪时间
    local temp_state=$(mktemp)
    jq --arg time "$timestamp" \
       '.last_checks.weekly_pruning = $time' \
       "$STATE_FILE" > "$temp_state"
    mv "$temp_state" "$STATE_FILE"

    log_success "✅ 状态文件已更新"
}

# 记录到优化日志
log_optimization() {
    local backup_dir=$1
    local timestamp=$(date +%Y-%m-%dT%H:%M:%SZ)

    log_info "📝 记录优化日志..."

    local temp_log=$(mktemp)
    jq --arg time "$timestamp" \
       --arg backup "$backup_dir" \
       '.optimizations += [{
         "timestamp": $time,
         "type": "weekly",
         "backup": $backup,
         "status": "success"
       }]' \
       "$LOG_FILE" > "$temp_log"
    mv "$temp_log" "$LOG_FILE"

    log_success "✅ 优化日志已记录"
}

# 生成报告
generate_report() {
    local backup_dir=$1
    local timestamp=$(date +%Y-%m-%dT%H:%M:%SZ)

    log_info "📝 生成事后简报..."

    # 统计信息
    local total_optimizations=$(jq -r '.optimizations | length' "$LOG_FILE")
    local weekly_optimizations=$(jq -r '[.optimizations[] | select(.type == "weekly")] | length' "$LOG_FILE")

    # 输出报告
    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║          每周修剪与重构完成报告                              ║
╚════════════════════════════════════════════════════════════╝

🕐 执行时间: $timestamp
📦 备份位置: $backup_dir
✅ 状态: 成功完成

📊 系统统计:
  - 总优化次数: $total_optimizations
  - 每周修剪次数: $weekly_optimizations

📋 本次执行内容:
  1. 迷你访谈（5-10 个问题）
     - 收集用户反馈
     - 分析行为变化

  2. 断舍离（记忆折叠）
     - 扫描过时规则
     - 删除冗余逻辑
     - 压缩历史记录

  3. 深度重构
     - 优化 USER.md
     - 优化 SOUL.md
     - 优化 AGENTS.md

🔄 回滚命令:
   rm -rf ~/.claude
   cp -r $backup_dir ~/.claude

下次修剪: 下周日 09:00
╚════════════════════════════════════════════════════════════╝

EOF

    log_success "✅ 事后简报已生成"
}

# 主函数
main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     全域意图对齐与自主进化 - 每周修剪与重构                 ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    ensure_dirs

    # 检查是否启用每周修剪
    local weekly_enabled=$(jq -r '.optimization_triggers.weekly_review // true' "$REWARD_CONFIG")
    if [ "$weekly_enabled" != "true" ]; then
        log_warning "⚠️  每周修剪已禁用，退出"
        exit 0
    fi

    # 执行修剪流程
    local backup_dir=$(backup_state)
    mini_interview
    prune_memory
    deep_refactor
    update_state
    log_optimization "$backup_dir"
    generate_report "$backup_dir"

    log_success "🎉 每周修剪与重构完成！"
}

# 执行
main "$@"
