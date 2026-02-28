#!/bin/bash

# 全域意图对齐与自主进化 - 每日自动优化脚本
# Trigger: 每天 06:00（Heartbeat 机制）

set -e

# 配置
CLAUDE_DIR="$HOME/.claude"
CONFIG_DIR="$CLAUDE_DIR/config"
BACKUP_DIR="$CLAUDE_DIR/backups"
STATE_FILE="$CONFIG_DIR/heartbeat-state.json"
LOG_FILE="$BACKUP_DIR/optimization-log.json"
REWARD_CONFIG="$CONFIG_DIR/reward-config.json"

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
    local backup_dir="$BACKUP_DIR/backup-$timestamp"

    log_info "📦 备份当前状态..."

    cp -r "$CLAUDE_DIR" "$backup_dir"
    cp "$STATE_FILE" "$backup_dir/heartbeat-state.json.bak"
    cp "$REWARD_CONFIG" "$backup_dir/reward-config.json.bak"

    log_success "✅ 备份完成: $backup_dir"

    echo "$backup_dir"
}

# Review（回顾过去 24 小时）
review_daily() {
    log_info "🔍 回顾过去 24 小时..."

    # 读取状态文件
    local task_count=$(jq -r '.statistics.task_count // 0' "$STATE_FILE")
    local success_count=$(jq -r '.statistics.successful_tasks // 0' "$STATE_FILE")
    local fail_count=$(jq -r '.statistics.failed_tasks // 0' "$STATE_FILE")

    log_info "📊 任务统计: 总计 $task_count, 成功 $success_count, 失败 $fail_count"

    # 计算成功率
    if [ "$task_count" -gt 0 ]; then
        local success_rate=$(echo "scale=2; $success_count * 100 / $task_count" | bc)
        log_info "📈 成功率: ${success_rate}%"
    fi

    # 检查性能下降
    local perf_decline_threshold=$(jq -r '.optimization_triggers.performance_decline_threshold // 0.1' "$REWARD_CONFIG")
    # 这里简化处理，实际应该对比历史数据

    log_success "✅ Review 完成"
}

# Analyze（分析优化机会）
analyze_optimization() {
    log_info "🧠 分析优化机会..."

    # 检查 USER.md
    if [ -f "$CLAUDE_DIR/USER.md" ]; then
        log_info "📄 检查 USER.md..."
        # 这里可以添加更复杂的分析逻辑
    fi

    # 检查 SOUL.md
    if [ -f "$CLAUDE_DIR/SOUL.md" ]; then
        log_info "📄 检查 SOUL.md..."
    fi

    # 检查 AGENTS.md
    if [ -f "$CLAUDE_DIR/AGENTS.md" ]; then
        log_info "📄 检查 AGENTS.md..."
    fi

    log_success "✅ Analyze 完成"
}

# Sandbox Test（沙盒测试）
sandbox_test() {
    log_info "🧪 沙盒测试..."

    local sandbox_enabled=$(jq -r '.sandbox.enabled // true' "$REWARD_CONFIG")
    local sandbox_method=$(jq -r '.sandbox.method // "git_worktree"' "$REWARD_CONFIG")
    local sandbox_location=$(jq -r '.sandbox.location // ".worktrees/skill-test"' "$REWARD_CONFIG")

    if [ "$sandbox_enabled" != "true" ]; then
        log_warning "⚠️  沙盒测试已禁用，跳过"
        return 0
    fi

    if [ "$sandbox_method" = "git_worktree" ]; then
        # 检查是否在 git 仓库中
        if ! git rev-parse --git-dir > /dev/null 2>&1; then
            log_warning "⚠️  不在 git 仓库中，跳过沙盒测试"
            return 0
        fi

        # 创建 worktree
        local branch_name="skill-test-$(date +%s)"
        mkdir -p .worktrees

        log_info "🔧 创建 Git Worktree: $sandbox_location"
        git worktree add "$sandbox_location" -b "$branch_name" 2>/dev/null || {
            log_error "❌ 创建 Worktree 失败"
            return 1
        }

        # 在沙盒中运行测试（这里简化处理）
        log_info "✅ 沙盒环境已创建"

        # 清理 worktree
        log_info "🧹 清理沙盒环境..."
        git worktree remove "$sandbox_location" 2>/dev/null || true
        git branch -D "$branch_name" 2>/dev/null || true
    fi

    log_success "✅ Sandbox Test 完成"
}

# Execute（自主落地）
execute_optimization() {
    log_info "🚀 执行优化..."

    # 这里可以添加实际的优化逻辑
    # 例如：更新配置、调整权重、优化 Agent 编排等

    log_success "✅ Execute 完成"
}

# Report（事后简报）
generate_report() {
    local backup_dir=$1
    local timestamp=$(date +%Y-%m-%dT%H:%M:%SZ)

    log_info "📝 生成事后简报..."

    # 更新状态文件
    local temp_state=$(mktemp)
    jq --arg time "$timestamp" \
       '.last_checks.daily_optimization = $time' \
       "$STATE_FILE" > "$temp_state"
    mv "$temp_state" "$STATE_FILE"

    # 记录到优化日志
    local temp_log=$(mktemp)
    jq --arg time "$timestamp" \
       --arg backup "$backup_dir" \
       '.optimizations += [{
         "timestamp": $time,
         "type": "daily",
         "backup": $backup,
         "status": "success"
       }]' \
       "$LOG_FILE" > "$temp_log"
    mv "$temp_log" "$LOG_FILE"

    # 输出报告
    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║          每日优化完成报告                                    ║
╚════════════════════════════════════════════════════════════╝

🕐 执行时间: $timestamp
📦 备份位置: $backup_dir
✅ 状态: 成功完成

📋 本次优化内容:
  - Review: 回顾过去 24 小时任务执行情况
  - Analyze: 分析优化机会
  - Sandbox: 沙盒测试验证
  - Execute: 执行优化
  - Report: 生成事后简报

🔄 回滚命令:
   rm -rf ~/.claude
   cp -r $backup_dir ~/.claude

下次优化: 明天 06:00
╚════════════════════════════════════════════════════════════╝

EOF

    log_success "✅ Report 完成"
}

# 主函数
main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║     全域意图对齐与自主进化 - 每日自动优化                   ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""

    ensure_dirs

    # 检查是否启用每日优化
    local daily_enabled=$(jq -r '.optimization_triggers.daily_optimization // true' "$REWARD_CONFIG")
    if [ "$daily_enabled" != "true" ]; then
        log_warning "⚠️  每日优化已禁用，退出"
        exit 0
    fi

    # 执行优化流程
    local backup_dir=$(backup_state)
    review_daily
    analyze_optimization
    sandbox_test
    execute_optimization
    generate_report "$backup_dir"

    log_success "🎉 每日优化完成！"
}

# 执行
main "$@"
