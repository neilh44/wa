#!/bin/bash

# Updated WhatsApp API Syntax Error Fix Script
# This script detects and fixes syntax errors in the WhatsApp API file

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}==== WhatsApp API Syntax Error Fix ====${NC}"

# Use the full path to the WhatsApp API file
WHATSAPP_API_FILE="/Users/nileshhanotia/Projects/Whatspp_GDrive/whatsapp-supabase-backend/app/api/whatsapp.py"
BACKUP_FILE="${WHATSAPP_API_FILE}.backup_$(date +%Y%m%d%H%M%S)"

# Check if the file exists
if [ ! -f "$WHATSAPP_API_FILE" ]; then
    echo -e "${RED}Error: File $WHATSAPP_API_FILE not found!${NC}"
    echo -e "${YELLOW}Please verify the path to your WhatsApp API file.${NC}"
    exit 1
fi

# Create a backup of the current file
cp "$WHATSAPP_API_FILE" "$BACKUP_FILE"
echo -e "${GREEN}Created backup at $BACKUP_FILE${NC}"

# Check for syntax errors in the file
echo -e "${YELLOW}Checking for syntax errors...${NC}"
SYNTAX_CHECK=$(python3 -c "import ast; ast.parse(open('$WHATSAPP_API_FILE').read())" 2>&1)

if [ $? -ne 0 ]; then
    echo -e "${RED}Syntax error detected:${NC}"
    echo "$SYNTAX_CHECK"
    
    # Display the problematic line for better understanding
    LINE_NUMBER=$(echo "$SYNTAX_CHECK" | grep -oP 'line \K[0-9]+' || echo "unknown")
    if [ "$LINE_NUMBER" != "unknown" ]; then
        echo -e "${YELLOW}Problematic line (${LINE_NUMBER}):${NC}"
        sed -n "${LINE_NUMBER}p" "$WHATSAPP_API_FILE" || echo "Could not display the line"
        
        # Also show a few lines before and after for context
        CONTEXT_START=$((LINE_NUMBER - 3))
        CONTEXT_END=$((LINE_NUMBER + 3))
        if [ $CONTEXT_START -lt 1 ]; then CONTEXT_START=1; fi
        
        echo -e "${YELLOW}Context (lines ${CONTEXT_START}-${CONTEXT_END}):${NC}"
        sed -n "${CONTEXT_START},${CONTEXT_END}p" "$WHATSAPP_API_FILE" || echo "Could not display context"
    fi
    
    # Look specifically for unterminated string literals
    if echo "$SYNTAX_CHECK" | grep -q "unterminated string literal"; then
        echo -e "${YELLOW}Detected unterminated string literal. Attempting to fix...${NC}"
        
        # Manual fix for the specific issue we know about
        if [ "$LINE_NUMBER" != "unknown" ]; then
            # Find the line with traceback.format_exc().split(" and fix it
            sed -i '' "${LINE_NUMBER}s/traceback\.format_exc()\.split(\"/traceback.format_exc().split(\"\\\\n\"/g" "$WHATSAPP_API_FILE" || echo "Failed to apply automatic fix"
            
            # Check if fix was successful
            SYNTAX_CHECK_AFTER=$(python3 -c "import ast; ast.parse(open('$WHATSAPP_API_FILE').read())" 2>&1)
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Syntax error fixed successfully!${NC}"
                echo -e "${YELLOW}Fixed line now reads:${NC}"
                sed -n "${LINE_NUMBER}p" "$WHATSAPP_API_FILE"
                echo -e "${GREEN}You can now restart your server.${NC}"
            else
                echo -e "${RED}Simple fix attempt failed. Trying more comprehensive fix...${NC}"
                
                # Create a Python script for more comprehensive fix
                cat > fix_syntax.py << 'EOL'
import re
import sys

def fix_unterminated_strings(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Replace problematic JSONResponse section
    json_response_pattern = r'(return JSONResponse\(\s*status_code=status\.HTTP_500_INTERNAL_SERVER_ERROR,\s*content=\{\s*"detail": str\(e\),\s*"type": type\(e\)\.__name__,\s*)"traceback": traceback\.format_exc\(\)\.split\(([^)]*)'
    replacement = r'\1"traceback": traceback.format_exc().split("\\n")'
    
    fixed_content = re.sub(json_response_pattern, replacement, content)
    
    # Write the fixed content back to the file
    with open(file_path, 'w') as file:
        file.write(fixed_content)
    
    return "Fixed unterminated string literals in the file."

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_syntax.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    print(fix_unterminated_strings(file_path))
EOL

                # Run the Python script for a more comprehensive fix
                echo -e "${YELLOW}Running comprehensive fix script...${NC}"
                python3 fix_syntax.py "$WHATSAPP_API_FILE"
                
                # Verify the fix again
                SYNTAX_CHECK_AFTER=$(python3 -c "import ast; ast.parse(open('$WHATSAPP_API_FILE').read())" 2>&1)
                
                if [ $? -eq 0 ]; then
                    echo -e "${GREEN}Syntax error fixed successfully with comprehensive fix!${NC}"
                    echo -e "${GREEN}You can now restart your server.${NC}"
                else
                    echo -e "${RED}Comprehensive fix also failed. Manual editing required.${NC}"
                    echo -e "${YELLOW}Restoring backup...${NC}"
                    cp "$BACKUP_FILE" "$WHATSAPP_API_FILE"
                    
                    echo -e "${RED}Please manually edit the file:${NC}"
                    echo "1. Open the file in a text editor: $WHATSAPP_API_FILE"
                    echo "2. Go to line $LINE_NUMBER"
                    echo "3. Look for the unterminated string near 'traceback.format_exc().split(\"'"
                    echo "4. Fix it to be: traceback.format_exc().split(\"\\n\")"
                    echo "5. Save and try running the server again"
                fi
            fi
        else
            echo -e "${RED}Could not determine line number. Manual fix required.${NC}"
        fi
    else
        # Handle other types of syntax errors
        echo -e "${RED}Unknown syntax error. Manual fix required.${NC}"
        echo -e "${YELLOW}Please check the file $WHATSAPP_API_FILE manually.${NC}"
    fi
else
    echo -e "${GREEN}No syntax errors detected in $WHATSAPP_API_FILE${NC}"
    
    # Still check for potential formatting issues in the traceback line
    echo -e "${YELLOW}Checking for potential formatting issues...${NC}"
    
    # Look for traceback.format_exc().split(" without proper closure
    if grep -q 'traceback\.format_exc()\.split("' "$WHATSAPP_API_FILE" && ! grep -q 'traceback\.format_exc()\.split("\\n"' "$WHATSAPP_API_FILE"; then
        echo -e "${YELLOW}Found potential issue with traceback.format_exc().split() formatting.${NC}"
        echo -e "${YELLOW}Applying preventative fix...${NC}"
        
        # Use sed to replace the problematic pattern (macOS compatible)
        sed -i '' 's/traceback\.format_exc()\.split("/traceback.format_exc().split("\\\\n"/g' "$WHATSAPP_API_FILE"
        
        echo -e "${GREEN}Applied preventative fix. This should prevent future issues.${NC}"
    else
        echo -e "${GREEN}No potential formatting issues detected.${NC}"
    fi
fi

# Clean up temporary files
rm -f fix_syntax.py

echo -e "${GREEN}Script completed. You can now restart your server.${NC}"
echo -e "${YELLOW}If you encounter further issues, the backup file is available at: $BACKUP_FILE${NC}"