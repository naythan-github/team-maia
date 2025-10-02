#!/bin/bash
# Continue Command Protection Hook
# Specifically triggers when user types "continue" and token overflow occurs
# Forces Sonnet usage to prevent automatic Opus escalation

echo ""
echo "🚨 CONTINUE COMMAND DETECTED - Model Enforcement Active"
echo "💡 Token overflow often triggers unwanted Opus usage"
echo ""

# Check if this is a continue/token overflow scenario
if [[ "${USER_INPUT,,}" =~ ^(continue|cont|more|keep going|carry on)$ ]] || [[ "$CLAUDE_TOKEN_OVERFLOW" == "true" ]]; then
    echo "🔒 CONTINUE ENFORCEMENT ACTIVATED"
    echo "   ⚡ Forcing Sonnet usage to prevent Opus escalation"
    echo "   💰 Estimated savings: \$0.06 per prevented Opus session"
    echo ""
    
    # Log the enforcement action
    python3 /Users/naythan/git/maia/claude/hooks/model_enforcement_webhook.py --continue-command
    
    # Set environment variable to force Sonnet
    export CLAUDE_FORCE_MODEL="sonnet"
    export CLAUDE_BLOCK_OPUS="true"
    
    echo "✅ Model enforcement applied: Sonnet locked for continue commands"
    echo ""
else
    echo "ℹ️  Standard model selection applies"
fi

# Additional protection for common token overflow patterns
if [[ "${USER_INPUT,,}" =~ (finish|complete|elaborate|expand|detail) ]]; then
    echo "⚠️  Detected potential token overflow request"
    echo "   🎯 Recommending Sonnet for completion tasks"
    export CLAUDE_RECOMMEND_SONNET="true"
fi