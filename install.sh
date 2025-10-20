#!/usr/bin/env bash
#
# Dotfiles Installation Script
#
# Installs dotfiles including:
# - Vim configuration
# - Claude Code configuration and skills
# - Conversation memory system with semantic search
#
# Usage:
#   ./install.sh           # Install everything
#   ./install.sh --help    # Show help

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the absolute path to the dotfiles directory
DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Backup directory for existing files
BACKUP_DIR="$HOME/.dotfiles-backup-$(date +%Y%m%d-%H%M%S)"

# Track what was installed for summary
INSTALLED=()
SKIPPED=()
BACKED_UP=()

################################################################################
# Helper Functions
################################################################################

print_header() {
    echo -e "${BLUE}==>${NC} ${1}"
}

print_success() {
    echo -e "${GREEN}✓${NC} ${1}"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} ${1}"
}

print_error() {
    echo -e "${RED}✗${NC} ${1}"
}

print_info() {
    echo -e "  ${1}"
}

backup_file() {
    local file="$1"
    if [ -e "$file" ] && [ ! -L "$file" ]; then
        mkdir -p "$BACKUP_DIR"
        cp -R "$file" "$BACKUP_DIR/"
        BACKED_UP+=("$(basename "$file")")
        print_info "Backed up $(basename "$file") to $BACKUP_DIR"
        return 0
    fi
    return 1
}

create_symlink() {
    local source="$1"
    local target="$2"
    local name="$3"

    # If target exists and is already the correct symlink, skip
    if [ -L "$target" ] && [ "$(readlink "$target")" = "$source" ]; then
        print_info "$name already linked correctly"
        SKIPPED+=("$name")
        return 0
    fi

    # Backup existing file/directory if it exists and isn't a symlink
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        backup_file "$target"
    fi

    # Remove existing symlink if it points elsewhere
    if [ -L "$target" ]; then
        rm "$target"
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$target")"

    # Create symlink
    ln -sf "$source" "$target"
    print_success "Linked $name"
    INSTALLED+=("$name")
}

check_command() {
    local cmd="$1"
    local name="$2"
    local install_hint="$3"

    if ! command -v "$cmd" &> /dev/null; then
        print_error "$name is required but not installed"
        if [ -n "$install_hint" ]; then
            print_info "$install_hint"
        fi
        return 1
    fi
    return 0
}

################################################################################
# Main Installation Functions
################################################################################

check_prerequisites() {
    print_header "Checking prerequisites"

    local all_found=true

    if check_command "node" "Node.js" "Install from https://nodejs.org or use nvm"; then
        print_info "Node.js $(node --version)"
    else
        all_found=false
    fi

    if check_command "npm" "npm" "Comes with Node.js"; then
        print_info "npm $(npm --version)"
    else
        all_found=false
    fi

    if ! $all_found; then
        print_error "Missing required prerequisites"
        exit 1
    fi

    print_success "All prerequisites found"
    echo
}

install_vim() {
    print_header "Installing Vim configuration"

    create_symlink \
        "$DOTFILES_DIR/vimrc" \
        "$HOME/.vimrc" \
        "vimrc"

    echo
}

install_skills_flattened() {
    print_info "Installing skills with flattened structure..."

    # Create skills directory
    mkdir -p "$HOME/.claude/skills"

    # Remove old symlink if it exists
    if [ -L "$HOME/.claude/skills" ]; then
        rm "$HOME/.claude/skills"
        mkdir -p "$HOME/.claude/skills"
    fi

    # Find all SKILL.md files in nested directories and create individual symlinks
    local skills_source="$DOTFILES_DIR/.claude/skills"
    local skill_count=0

    # Find all directories containing SKILL.md files
    while IFS= read -r -d '' skill_md; do
        local skill_dir=$(dirname "$skill_md")
        local skill_name=$(basename "$skill_dir")

        # Create symlink from ~/.claude/skills/skill-name to the actual location
        create_symlink \
            "$skill_dir" \
            "$HOME/.claude/skills/$skill_name" \
            "skills/$skill_name"

        ((skill_count++))
    done < <(find "$skills_source" -name "SKILL.md" -print0)

    if [ $skill_count -eq 0 ]; then
        print_warning "No skills found in $skills_source"
    else
        print_success "Installed $skill_count skill(s) with flattened structure"
    fi
}

install_claude() {
    print_header "Installing Claude Code configuration"

    # Create ~/.claude directory if it doesn't exist
    mkdir -p "$HOME/.claude"

    # Link CLAUDE.md
    create_symlink \
        "$DOTFILES_DIR/.claude/CLAUDE.md" \
        "$HOME/.claude/CLAUDE.md" \
        "CLAUDE.md"

    # Link commands directory
    create_symlink \
        "$DOTFILES_DIR/.claude/commands" \
        "$HOME/.claude/commands" \
        "commands/"

    # Install skills with flattened structure
    install_skills_flattened

    # Link mcp directory
    create_symlink \
        "$DOTFILES_DIR/.claude/mcp" \
        "$HOME/.claude/mcp" \
        "mcp/"

    echo
}

install_conversation_memory() {
    print_header "Installing conversation memory system"

    # Check if skills directory is linked
    if [ ! -d "$HOME/.claude/skills/remembering-conversations" ]; then
        print_error "Skills directory not found. Run install_claude first."
        return 1
    fi

    local tool_dir="$HOME/.claude/skills/remembering-conversations/tool"

    # Install npm dependencies
    print_info "Installing Node.js dependencies (this may take a minute)..."
    if (cd "$tool_dir" && npm install --silent > /dev/null 2>&1); then
        print_success "Installed conversation search dependencies"
        INSTALLED+=("conversation-search npm packages")
    else
        print_warning "Failed to install npm dependencies"
        print_info "You can install manually: cd $tool_dir && npm install"
    fi

    # Install sessionEnd hook
    print_info "Installing conversation indexing hook..."
    if "$tool_dir/install-hook" > /dev/null 2>&1; then
        print_success "Installed sessionEnd hook"
        INSTALLED+=("sessionEnd hook")
    else
        print_warning "Failed to install sessionEnd hook"
        print_info "You can install manually: $tool_dir/install-hook"
    fi

    echo
}

install_chrome_mcp() {
    print_header "Installing Chrome MCP Server"

    # Check if mcp directory is linked
    if [ ! -d "$HOME/.claude/mcp/chrome" ]; then
        print_error "MCP directory not found. Run install_claude first."
        return 1
    fi

    local mcp_dir="$HOME/.claude/mcp/chrome"

    # Install npm dependencies and build
    print_info "Installing Node.js dependencies and building MCP server..."
    if (cd "$mcp_dir" && npm install --silent > /dev/null 2>&1 && npm run build --silent > /dev/null 2>&1); then
        print_success "Built Chrome MCP server"
        INSTALLED+=("chrome-mcp-server")
    else
        print_warning "Failed to build Chrome MCP server"
        print_info "You can build manually: cd $mcp_dir && npm install && npm run build"
    fi

    echo
}

configure_mcp_servers() {
    print_header "Configuring Chrome MCP Server"

    # Chrome MCP server configuration
    local chrome_config='{
  "mcpServers": {
    "chrome": {
      "command": "node",
      "args": ["'"$HOME"'/.claude/mcp/chrome/dist/index.js"]
    }
  }
}'

    # Configure Claude Code CLI (~/.claude.json)
    local cli_config="$HOME/.claude.json"
    print_info "Configuring Claude Code CLI ($cli_config)..."

    if configure_json_file "$cli_config" "$chrome_config"; then
        print_success "Configured Chrome MCP for Claude Code CLI"
        INSTALLED+=("chrome MCP config (CLI)")
    else
        print_warning "Could not auto-configure CLI - manual setup needed"
    fi

    # Configure Claude Desktop (macOS only for now)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        local desktop_config="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
        print_info "Configuring Claude Desktop ($desktop_config)..."

        if configure_json_file "$desktop_config" "$chrome_config"; then
            print_success "Configured Chrome MCP for Claude Desktop"
            INSTALLED+=("chrome MCP config (Desktop)")
        else
            print_warning "Could not auto-configure Desktop - manual setup needed"
        fi
    fi

    echo
}

configure_json_file() {
    local config_file="$1"
    local new_config="$2"

    # Create directory if it doesn't exist
    local config_dir=$(dirname "$config_file")
    mkdir -p "$config_dir" 2>/dev/null || return 1

    # Use Node.js to merge JSON configurations
    node <<EOF 2>/dev/null
const fs = require('fs');
const configFile = '$config_file';
const newConfig = $new_config;

let existing = { mcpServers: {} };

// Read existing config if it exists
if (fs.existsSync(configFile)) {
    try {
        const content = fs.readFileSync(configFile, 'utf8');
        existing = JSON.parse(content);
        if (!existing.mcpServers) {
            existing.mcpServers = {};
        }
    } catch (e) {
        console.error('Error parsing existing config:', e.message);
        process.exit(1);
    }
}

// Merge chrome MCP config (preserve existing servers)
existing.mcpServers = {
    ...existing.mcpServers,
    ...newConfig.mcpServers
};

// Write updated config
try {
    fs.writeFileSync(configFile, JSON.stringify(existing, null, 2) + '\n', 'utf8');
    process.exit(0);
} catch (e) {
    console.error('Error writing config:', e.message);
    process.exit(1);
}
EOF

    return $?
}

print_summary() {
    echo
    print_header "Installation Summary"
    echo

    if [ ${#INSTALLED[@]} -gt 0 ]; then
        print_success "Installed ${#INSTALLED[@]} component(s):"
        for item in "${INSTALLED[@]}"; do
            print_info "• $item"
        done
        echo
    fi

    if [ ${#SKIPPED[@]} -gt 0 ]; then
        print_info "Skipped ${#SKIPPED[@]} component(s) (already installed):"
        for item in "${SKIPPED[@]}"; do
            print_info "• $item"
        done
        echo
    fi

    if [ ${#BACKED_UP[@]} -gt 0 ]; then
        print_warning "Backed up ${#BACKED_UP[@]} existing file(s):"
        for item in "${BACKED_UP[@]}"; do
            print_info "• $item"
        done
        print_info "Backups saved to: $BACKUP_DIR"
        echo
    fi

    print_header "Next Steps"
    echo
    print_info "1. Restart your terminal or run: source ~/.bashrc (or ~/.zshrc)"
    print_info "2. Restart Claude Code CLI or Claude Desktop to load MCP configuration"
    print_info "3. Open vim to verify configuration"
    print_info "4. Start a Claude Code session - conversations will be automatically archived"
    print_info "5. Search past conversations: ~/.claude/skills/remembering-conversations/tool/search-conversations \"query\""
    echo
    print_info "For more details, see README.md"
    echo

    print_success "Installation complete!"
}

show_help() {
    cat << EOF
Dotfiles Installation Script

USAGE:
    ./install.sh [OPTIONS]

OPTIONS:
    --help, -h      Show this help message

DESCRIPTION:
    Installs dotfiles including:
    - Vim configuration (vimrc)
    - Claude Code configuration and commands
    - Claude Code skills (TDD, conversation memory, browser automation)
    - Conversation memory system with semantic search
    - Chrome MCP server for browser automation

    The script will:
    1. Check prerequisites (Node.js, npm)
    2. Backup any existing files before overwriting
    3. Create symlinks from your home directory to this repo
    4. Install conversation search dependencies (npm packages)
    5. Install sessionEnd hook for automatic conversation archiving
    6. Build Chrome MCP server for browser automation
    7. Configure MCP settings for both Claude Code CLI and Desktop

SAFETY:
    - All existing files are backed up before replacement
    - Existing correct symlinks are preserved
    - Can be run multiple times safely (idempotent)
    - Backups stored in ~/.dotfiles-backup-TIMESTAMP/

EXAMPLES:
    # Standard installation
    ./install.sh

    # Show help
    ./install.sh --help

PREREQUISITES:
    - Node.js (v16+)
    - npm
    - git (to clone this repo)

EOF
}

################################################################################
# Main
################################################################################

main() {
    # Parse arguments
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        "")
            # No arguments, proceed with installation
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Run './install.sh --help' for usage"
            exit 1
            ;;
    esac

    echo
    print_header "Dotfiles Installation"
    print_info "Installing from: $DOTFILES_DIR"
    echo

    # Run installation steps
    check_prerequisites
    install_vim
    install_claude
    install_conversation_memory
    install_chrome_mcp
    configure_mcp_servers

    # Show summary
    print_summary
}

# Run main function
main "$@"
