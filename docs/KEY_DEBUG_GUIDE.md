# Key Press Debug Guide

## What Was Added

Comprehensive debug logging for all key presses and actions to diagnose why copy/move/delete operations aren't working.

## Debug Output at Startup

When the app starts, you'll see in `rclonecommander_debug.log`:

```
================================================================================
KEY BINDINGS CONFIGURED:
  Copy:   f5 -> action_copy
  Move:   f6 -> action_move
  Delete: f8,delete -> action_delete
  Remote: f10 -> action_select_remote
  Switch: tab -> action_switch_panel
  Swap:   ctrl+u -> action_swap_panels
  Quit:   q -> quit
================================================================================
```

This confirms which keys are configured for which actions.

## Debug Output When Pressing Keys

Every key press is now logged:

```
============================================================
KEY PRESSED: key='f5' character=''
  Modifiers: ctrl=False shift=False
  ✓ MATCHES binding for action: copy
    Full binding: f5
============================================================
```

This shows:
- What key was detected
- What character it represents
- Which action it should trigger

## Debug Output When Actions Are Called

When an action is actually invoked, you'll see:

```
================================================================================
ACTION CALLED: action_copy
================================================================================
action_copy: START
action_copy: src_panel=rclonecommander, dst_panel=local
action_copy: 1 entries selected
action_copy: Copying 'filename'
  src_path: rclonecommander:path/filename
  dst_path: local:path
  result: SUCCESS
action_copy: Successfully copied 1 item(s)
action_copy: END
```

## How to Diagnose Issues

### Issue 1: Key Not Detected
If you press a key and see NO log entry, the key press isn't reaching the app.

**Log shows:**
```
(nothing - no KEY PRESSED entry)
```

**Possible causes:**
- Terminal is capturing the key
- Textual isn't running
- Key is being handled by system

**Try:**
- Use F5/F6/F8 instead of Ctrl+C/X/D
- Check if other keys work (like Tab, Q)

### Issue 2: Key Detected But No Match
If you see a KEY PRESSED entry but no "MATCHES binding" line:

**Log shows:**
```
KEY PRESSED: key='c' character='c'
  Modifiers: ctrl=False shift=False
(no MATCHES line)
```

**Cause:** The key format doesn't match the binding format.

**Solution:** The binding format needs adjustment.

### Issue 3: Key Matches But Action Not Called
If you see "MATCHES binding" but no "ACTION CALLED" line:

**Log shows:**
```
KEY PRESSED: key='f5' character=''
  ✓ MATCHES binding for action: copy
============================================================
(no ACTION CALLED line)
```

**Cause:** Textual isn't routing the key to the action.

**Possible issues:**
- Binding syntax is wrong
- Key is being consumed by another widget
- Action method name doesn't match

### Issue 4: Action Called But Fails
If you see "ACTION CALLED" but operation fails:

**Log shows:**
```
ACTION CALLED: action_copy
action_copy: START
action_copy: No active panel
```

**Cause:** The operation is being called but conditions aren't met.

**Check:**
- Is a panel focused?
- Are files selected?
- Is destination valid?

## Testing Steps

1. **Start the app** and check the log for "KEY BINDINGS CONFIGURED"
2. **Select a file** with Space
3. **Press Ctrl+C** to copy
4. **Check the log** for:
   - KEY PRESSED entry
   - MATCHES binding entry
   - ACTION CALLED entry
   - Operation details

## Expected Full Sequence

For a successful copy operation, you should see:

```
# At startup
KEY BINDINGS CONFIGURED:
  Copy:   f5 -> action_copy
  ...

# When pressing Space
KEY PRESSED: key='space' character=' '
  ✓ MATCHES binding for action: toggle_select
action_toggle_select: TRIGGERED at cursor_row=1
toggle_selection: START
...

# When pressing F5
KEY PRESSED: key='f5' character=''
  ✓ MATCHES binding for action: copy
    Full binding: f5
ACTION CALLED: action_copy
action_copy: START
action_copy: src_panel=rclonecommander, dst_panel=local
action_copy: 1 entries selected
action_copy: Copying 'filename'
  src_path: rclonecommander:gempa/filename
  dst_path: local:/Users/p/...
  result: SUCCESS
action_copy: END
```

## Common Issues & Solutions

### Ctrl+C Not Working

**If Ctrl+C is captured by terminal:**
- Try **F5** instead (alternative key for copy)
- Or use Ctrl+Shift+C if your terminal supports it

### No Files Selected

**Log shows:**
```
action_copy: 0 entries selected
action_copy: No entries to copy
```

**Solution:** Press Space on files first to select them.

### Wrong Panel Active

**Log shows:**
```
action_copy: No active panel
```

**Solution:** Click on the source panel first, or press Tab to switch panels.

## What to Look For

When you test and share the log, look for:

1. ✓ Key bindings are configured
2. ✓ Key presses are detected
3. ✓ Keys match the configured bindings
4. ✓ Actions are called
5. ? Operations complete successfully

If any of steps 1-4 don't show ✓ in the log, that's where the problem is!
