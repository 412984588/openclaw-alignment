#!/bin/bash

# 全域意图对齐与完全自主进化协议 - 一键安装脚本
# 适用于 macOS 和 Linux

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$HOME/.claude"
PROJECT_NAME="全域意图对齐与自主进化"

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
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 显示欢迎信息
show_welcome() {
    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║                                                              ║
║     全域意图对齐与完全自主进化协议 - 一键安装               ║
║                                                              ║
║     基于强化学习的 AI 协作系统                                ║
║     支持深度模式（历史数据建模）和快速模式（主动访谈）         ║
║                                                              ║
╚════════════════════════════════════════════════════════════╝

本安装脚本将会：
  1. 安装核心文件（USER.md, SOUL.md, AGENTS.md）
  2. 安装 OpenClaw Skill
  3. 配置奖励系统
  4. 设置自动化脚本
  5. 引导初始化

预计时间：2-3 分钟

按任意键继续...
EOF

    read -n 1 -s
    echo ""
}

# 检查系统要求
check_requirements() {
    log_step "检查系统要求"

    # 检查操作系统
    local os=$(uname -s)
    log_info "操作系统: $os"

    if [ "$os" != "Darwin" ] && [ "$os" != "Linux" ]; then
        log_error "不支持的操作系统: $os"
        exit 1
    fi

    # 检查必需命令
    local required_commands=("jq" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_warning "缺少必需命令: $cmd"
            log_info "正在尝试安装 $cmd..."

            if [ "$os" = "Darwin" ]; then
                # macOS
                if command -v brew &> /dev/null; then
                    brew install "$cmd"
                else
                    log_error "请先安装 Homebrew: https://brew.sh"
                    exit 1
                fi
            else
                # Linux
                if command -v apt-get &> /dev/null; then
                    sudo apt-get update && sudo apt-get install -y "$cmd"
                elif command -v yum &> /dev/null; then
                    sudo yum install -y "$cmd"
                else
                    log_error "无法自动安装 $cmd，请手动安装"
                    exit 1
                fi
            fi
        fi
    done

    log_success "✅ 系统要求检查通过"
}

# 创建目录结构
create_directories() {
    log_step "创建目录结构"

    local dirs=(
        "$CLAUDE_DIR"
        "$CLAUDE_DIR/skills"
        "$CLAUDE_DIR/config"
        "$CLAUDE_DIR/backups"
        "$CLAUDE_DIR/scripts"
    )

    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done

    log_success "✅ 目录结构创建完成"
}

# 安装核心文件
install_core_files() {
    log_step "安装核心文件"

    # 复制核心文件
    cp "$SCRIPT_DIR/USER.md" "$CLAUDE_DIR/"
    cp "$SCRIPT_DIR/SOUL.md" "$CLAUDE_DIR/"
    cp "$SCRIPT_DIR/AGENTS.md" "$CLAUDE_DIR/"

    log_success "✅ 核心文件安装完成"
}

# 安装 Skill
install_skill() {
    log_step "安装 OpenClaw Skill"

    # 复制 Skill 文件
    cp "$SCRIPT_DIR/skills/全域意图对齐与自主进化.md" "$CLAUDE_DIR/skills/"

    log_success "✅ Skill 安装完成"
}

# 安装配置文件
install_configs() {
    log_step "安装配置文件"

    # 复制配置文件
    cp "$SCRIPT_DIR/config/reward-config.json" "$CLAUDE_DIR/config/"
    cp "$SCRIPT_DIR/config/heartbeat-state.json" "$CLAUDE_DIR/config/"
    cp "$SCRIPT_DIR/config/interview-questions.json" "$CLAUDE_DIR/config/"

    log_success "✅ 配置文件安装完成"
}

# 安装脚本
install_scripts() {
    log_step "安装自动化脚本"

    # 复制脚本
    cp "$SCRIPT_DIR/scripts/daily-evolution.sh" "$CLAUDE_DIR/scripts/"
    cp "$SCRIPT_DIR/scripts/weekly-pruning.sh" "$CLAUDE_DIR/scripts/"
    cp "$SCRIPT_DIR/scripts/quick-mode-init.sh" "$CLAUDE_DIR/scripts/"

    # 添加执行权限
    chmod +x "$CLAUDE_DIR/scripts/"*.sh

    log_success "✅ 自动化脚本安装完成"
}

# 初始化数据文件
init_data_files() {
    log_step "初始化数据文件"

    # 复制优化日志（如果不存在）
    if [ ! -f "$CLAUDE_DIR/backups/optimization-log.json" ]; then
        cp "$SCRIPT_DIR/backups/optimization-log.json" "$CLAUDE_DIR/backups/"
    fi

    log_success "✅ 数据文件初始化完成"
}

# 配置定时任务（可选）
setup_cron() {
    log_step "配置定时任务（可选）"

    echo ""
    log_info "是否配置定时任务？"
    echo "  - 每日优化：每天 06:00 自动执行"
    echo "  - 每周修剪：每周日 09:00 自动执行"
    echo ""
    echo -n "配置定时任务？[y/N]: "
    read -r answer

    if [[ "$answer" =~ ^[Yy]$ ]]; then
        # 获取脚本路径
        local daily_script="$CLAUDE_DIR/scripts/daily-evolution.sh"
        local weekly_script="$CLAUDE_DIR/scripts/weekly-pruning.sh"

        # 创建临时 crontab
        local temp_cron=$(mktemp)

        # 添加现有 crontab（如果存在）
        if crontab -l &> /dev/null; then
            crontab -l > "$temp_cron"
        fi

        # 添加新任务
        echo "# 全域意图对齐与自主进化 - 每日优化" >> "$temp_cron"
        echo "0 6 * * * $daily_script >> $CLAUDE_DIR/logs/daily.log 2>&1" >> "$temp_cron"
        echo "" >> "$temp_cron"
        echo "# 全域意图对齐与自主进化 - 每周修剪" >> "$temp_cron"
        echo "0 9 * * 0 $weekly_script >> $CLAUDE_DIR/logs/weekly.log 2>&1" >> "$temp_cron"

        # 安装 crontab
        crontab "$temp_cron"
        rm "$temp_cron"

        log_success "✅ 定时任务配置完成"
    else
        log_info "跳过定时任务配置"
    fi
}

# 运行初始化向导
run_init_wizard() {
    log_step "运行初始化向导"

    echo ""
    log_info "现在需要选择初始化模式："
    echo "  1. 深度模式（有历史数据）- 自动建模"
    echo "  2. 快速模式（新设备）- 主动访谈"
    echo ""
    echo -n "请选择模式 [1/2]: "
    read -r mode

    if [ "$mode" = "1" ]; then
        log_info "启动深度模式..."
        # 深度模式需要扫描历史数据，这里暂时简化处理
        log_warning "深度模式需要手动扫描历史数据"
        log_info "你可以稍后运行：~/.claude/scripts/quick-mode-init.sh"
    else
        log_info "启动快速模式初始化..."
        bash "$CLAUDE_DIR/scripts/quick-mode-init.sh"
    fi
}

# 显示完成信息
show_completion() {
    cat <<EOF

╔════════════════════════════════════════════════════════════╗
║          安装完成！                                         ║
╚════════════════════════════════════════════════════════════╝

✅ 核心文件已安装到: $CLAUDE_DIR
✅ Skill 已安装
✅ 自动化脚本已就绪

📚 快速开始:
  1. 查看文档: cat $SCRIPT_DIR/README.md
  2. 主动优化: bash $CLAUDE_DIR/scripts/daily-evolution.sh
  3. 每周修剪: bash $CLAUDE_DIR/scripts/weekly-pruning.sh

📂 重要文件:
  - 用户画像: $CLAUDE_DIR/USER.md
  - 系统宪法: $CLAUDE_DIR/SOUL.md
  - 兵力编排: $CLAUDE_DIR/AGENTS.md
  - 奖励配置: $CLAUDE_DIR/config/reward-config.json

🔄 后续步骤:
  1. 根据你的使用习惯调整配置文件
  2. 运行初始化向导（如果还未运行）
  3. 开始使用 AI 协作系统

📖 完整文档: $SCRIPT_DIR/README.md

感谢使用全域意图对齐与完全自主进化协议！

EOF
}

# 主函数
main() {
    show_welcome
    check_requirements
    create_directories
    install_core_files
    install_skill
    install_configs
    install_scripts
    init_data_files
    setup_cron
    run_init_wizard
    show_completion

    log_success "🎉 安装完成！"
}

# 执行
main "$@"
