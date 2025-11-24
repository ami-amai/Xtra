#!/usr/bin/env python3
"""
V5.2 - FIXED patch for Xtra (use userLogin instead of userName for mentions)
Usage: python3 patch_xtra.py <path_to_Xtra_repository>
"""

import os
import sys
import re
from pathlib import Path

def apply_chatadapter_v52(file_path):
    """Patches ChatAdapter.kt with correct textView references"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Make sure onUsernameClick parameter exists in constructor
    if 'onUsernameClick' not in content:
        constructor_pattern = r'(private val channelId: String\?,)\s*(\n\s*\))'
        constructor_replacement = r'\1\n    private val onUsernameClick: ((String) -> Unit)? = null,\2'
        content = re.sub(constructor_pattern, constructor_replacement, content)
        print("✓ Added onUsernameClick parameter to constructor")
    else:
        print("⚠ onUsernameClick parameter already exists")
    
    # 2. Remove old incorrect code (GestureDetector or ClickableSpan)
    if 'gestureDetector' in content:
        # Remove entire GestureDetector block
        gesture_pattern = r'\s*val username = chatMessage\.userName.*?textView\.setOnTouchListener.*?\n\s+}'
        content = re.sub(gesture_pattern, '', content, flags=re.DOTALL)
        print("✓ Removed old GestureDetector code")
    
    if 'object : android.text.style.ClickableSpan()' in content:
        clickable_pattern = r'\s*// Добавляем ClickableSpan.*?holder\.bind'
        content = re.sub(clickable_pattern, 'holder.bind', content, flags=re.DOTALL)
        print("✓ Removed old ClickableSpan code")
    
    # 3. Add FIXED GestureDetector with correct references - use userLogin for mention
    viewholder_bind_pattern = r'(fun bind\(chatMessage: ChatMessage, formattedMessage: SpannableStringBuilder\) \{)'
    
    gesture_detector_code = r'''\1
        // Use userLogin for mentions (not userName which may contain emoji/kanji)
        val usernameForMention = chatMessage.userLogin ?: chatMessage.userName
        
        // GestureDetector for handling clicks on username
        val gestureDetector = android.view.GestureDetector(textView.context, object : android.view.GestureDetector.SimpleOnGestureListener() {
            override fun onSingleTapUp(e: android.view.MotionEvent): Boolean {
                if (usernameForMention != null && chatMessage.isReply == false) {
                    val layout = textView.layout
                    if (layout != null) {
                        val line = layout.getLineForVertical(e.y.toInt())
                        val offset = layout.getOffsetForHorizontal(line, e.x)
                        
                        // Check if clicked at the beginning of message (where username is)
                        if (offset < 30 && offset >= 0) {  // First 30 characters usually - username
                            onUsernameClick?.invoke(usernameForMention)
                            return true
                        }
                    }
                }
                return false
            }
            
            override fun onLongPress(e: android.view.MotionEvent) {
                if (chatMessage.isReply == false && textView.selectionStart == -1 && textView.selectionEnd == -1) {
                    selectedMessage = chatMessage
                    messageClickListener?.invoke(channelId)
                }
            }
        })
        
        textView.setOnTouchListener { _, event ->
            gestureDetector.onTouchEvent(event)
        }'''
    
    if 'gestureDetector' not in content:
        content = re.sub(viewholder_bind_pattern, gesture_detector_code, content)
        print("✓ Added fixed Motion Events handling via GestureDetector (uses userLogin)")
    else:
        print("⚠ GestureDetector already added")
    
    # Save only if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ File {file_path} successfully patched (V5.2)\n")
        return True
    else:
        print(f"ℹ️  File does not require changes\n")
        return False

def apply_chatfragment_v52(file_path):
    """Patches ChatFragment.kt"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 1. Make sure insertMentionAtCursor function exists
    if 'insertMentionAtCursor' not in content:
        insert_function = '''
    private fun insertMentionAtCursor(username: String) {
        with(binding) {
            val cursorPos = editText.selectionStart
            val text = editText.text ?: android.text.SpannableStringBuilder()
            
            text.insert(cursorPos, "@$username ")
            editText.setSelection(cursorPos + username.length + 2)
            editText.requestFocus()
            
            android.util.Log.d("ChatFragment", "Mention inserted: @$username at position $cursorPos")
        }
    }

'''
        toggle_pattern = r'(\s+fun toggleEmoteMenu\(enable: Boolean\))'
        if re.search(toggle_pattern, content):
            content = re.sub(toggle_pattern, insert_function + r'\1', content)
            print("✓ Added insertMentionAtCursor function")
        else:
            print("⚠ Could not find place for insertMentionAtCursor")
    else:
        print("⚠ insertMentionAtCursor function already exists")
    
    # 2. Make sure callback is passed to adapter
    if 'onUsernameClick' not in content:
        pattern = r'(channelId\s*=\s*channelId,)(\s*\))'
        if re.search(pattern, content):
            replacement = r'\1\n                        onUsernameClick = { username -> insertMentionAtCursor(username) },\2'
            content = re.sub(pattern, replacement, content)
            print("✓ Added onUsernameClick callback")
        else:
            print("⚠ Could not find adapter initialization")
    else:
        print("⚠ onUsernameClick callback already added")
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ File {file_path} successfully patched (V5.2)\n")
        return True
    else:
        print(f"ℹ️  File does not require changes\n")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 patch_xtra.py <path_to_Xtra_repository>")
        sys.exit(1)
    
    repo_path = Path(sys.argv[1])
    
    if not repo_path.exists():
        print(f"❌ Path does not exist")
        sys.exit(1)
    
    chatadapter_path = repo_path / "app" / "src" / "main" / "java" / "com" / "github" / "andreyasadchy" / "xtra" / "ui" / "chat" / "ChatAdapter.kt"
    chatfragment_path = repo_path / "app" / "src" / "main" / "java" / "com" / "github" / "andreyasadchy" / "xtra" / "ui" / "chat" / "ChatFragment.kt"
    
    if not chatadapter_path.exists() or not chatfragment_path.exists():
        print(f"❌ Files not found")
        sys.exit(1)
    
    print("=" * 70)
    print("Xtra Mention Patcher V5.2 - FIXED (userLogin for mentions)")
    print("=" * 70)
    print()
    
    print("📝 Patching ChatAdapter.kt (V5.2)...")
    adapter_patched = apply_chatadapter_v52(chatadapter_path)
    
    print("📝 Patching ChatFragment.kt (V5.2)...")
    fragment_patched = apply_chatfragment_v52(chatfragment_path)
    
    print("=" * 70)
    if adapter_patched or fragment_patched:
        print("✅ Patch V5.2 successfully applied!")
        print()
        print("Changes:")
        print("  • Use userLogin instead of userName for mentions")
        print("  • Emoji/Kanji usernames now mention correctly as login")
        print("  • Click on username → inserts @username (login)")
        print("  • Long press → opens dialog")
        print()
        print("Next steps:")
        print("  1. ./gradlew clean && ./gradlew assembleDebug")
        print("  2. adb install -r app/build/outputs/apk/debug/app-debug.apk")
        print("  3. Test with Kanji/Emoji usernames!")
    else:
        print("ℹ️  Re-patching not required")
    print("=" * 70)

if __name__ == "__main__":
    main()
