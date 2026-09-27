# Rubber-Ducky MCP Examples

Real-world usage examples of Claude Code with voice I/O.

## Example 1: Voice Email Triage

**You (speaking):** "Check my emails and tell me what's important"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe → "Check my emails and tell me what's important"
2. Reads emails using maildown MCP server
3. Analyzes for importance
4. Uses speak → "You have 3 important emails. The first is from..."
```

## Example 2: Voice Coding Assistant

**You (speaking):** "I need to refactor this function to use async/await"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe → "I need to refactor this function..."
2. Reads the code file
3. Generates refactored version
4. Uses speak → "I've refactored the function. Here's what changed..."
```

## Example 3: Voice Task Management

**You (speaking):** "Add a task to follow up with Julie about Dad's pension valuation"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe → "Add a task..."
2. Updates Daily Log
3. Uses speak → "Task added to today's TODO"
```

## Example 4: Continuous Voice Session

**Setup prompt:**
> "Let's have a voice conversation. I'll speak my requests, you'll listen using the listen tool and respond using the speak tool. Ready?"

**Conversation flow:**
```
You (speak): "What's on my calendar today?"
Claude: [listen] → [check calendar] → [speak] "You have 3 meetings today..."

You (speak): "Summarize the first one"
Claude: [listen] → [read details] → [speak] "Your 10am meeting is with..."

You (speak): "Thanks, that's all"
Claude: [listen] → [speak] "You're welcome!"
```

## Example 5: Voice Brainstorming

**Setup prompt:**
> "I want to brainstorm project ideas verbally. Listen to me describe the problem, then speak your suggestions back."

**Session:**
```
You (speak): "I need to build a tool that helps me organize my desktop files..."
Claude: [listen] → [think] → [speak] "I suggest a few approaches: First, a rule-based system..."

You (speak): "I like the second option. How would that work?"
Claude: [listen] → [speak] "The directory-based approach would work like this..."
```

## Example 6: Voice Code Review

**You (speaking):** "Review the changes I just made and give me feedback"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe
2. Runs git diff
3. Analyzes code changes
4. Uses speak → "I reviewed your changes. The new validation looks good, but I noticed the error handling could be improved..."
```

## Example 7: Hands-Free Research

**Setup prompt:**
> "I'm cooking dinner and need to research something. I'll ask questions verbally and you respond verbally."

**Session:**
```
You (speak): "What's the difference between MCP and REST APIs for local tools?"
Claude: [listen] → [research] → [speak] "Great question! MCP is better for local tools because..."

You (speak): "So which should I use for my project?"
Claude: [listen] → [speak] "Based on what you described, I'd recommend MCP because..."
```

## Example 8: Voice Dictation with Editing

**You (speaking):** "Take dictation for an email to Julie"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe (longer duration)
2. You dictate the email
3. Claude transcribes and formats
4. Uses speak → "I've drafted the email. Would you like me to read it back?"

You (speak): "Yes, read it"
Claude: [speak] → Reads the draft email
```

## Example 9: Debugging with Voice

**You (speaking):** "The tests are failing, help me debug"

**Claude Code workflow:**
```
1. Uses listen_and_transcribe
2. Runs tests, reads error output
3. Analyzes the problem
4. Uses speak → "I found the issue. The problem is in line 45 where..."
5. You ask follow-up questions verbally
6. Claude responds verbally until issue is resolved
```

## Example 10: Morning Briefing

**Setup prompt:**
> "Give me my morning briefing verbally. Check my calendar, emails, and tasks, then speak a summary."

**Claude Code workflow:**
```
1. Checks calendar (via calendar MCP)
2. Checks emails (via maildown MCP)
3. Checks Daily Log
4. Uses speak → "Good morning! Here's your briefing. You have 4 meetings today starting at 10am. You have 12 unread emails, 3 are important. Your top task today is..."
```

## Tips for Voice Sessions

### Best Practices

1. **Be explicit about voice mode:**
   > "Let's use voice - listen for my questions and speak your answers"

2. **Request confirmation for important actions:**
   > "Before you make any changes, speak back what you're about to do"

3. **Use natural language:**
   > "Hey, check my emails" (works better than formal commands)

4. **Background noise:** If in noisy environment, increase `silence_threshold`

### Useful Patterns

**Ask for summaries verbally:**
> "Summarize that in speech - I can't read right now"

**Dictation mode:**
> "Take dictation for the next 2 minutes, then read it back"

**Think-aloud debugging:**
> "Speak your reasoning as you debug this"

**Voice confirmations:**
> "Before running that command, tell me verbally what it will do"

## Advanced: Custom Voice Workflows

### Create a "Voice Coach" skill

```bash
# In your skills directory
cat > voice-coach.md << 'EOF'
# Voice Coach Skill

When user says "voice coach <topic>", start a voice coaching session:

1. Use listen_and_transcribe to hear their explanation
2. Provide verbal feedback using speak
3. Continue back-and-forth until they say "done"

Example: "voice coach speeding ticket" → helps prep for court
EOF
```

### Voice-Activated Context Loading

```bash
# Create a voice trigger for loading project context
"load dispatch" → [speak] "Loading fleetdispatch context..."
"load parents" → [speak] "Loading Dad's case context..."
```

## Performance Tips

1. **Shorter utterances = faster:** VAD will cut off sooner
2. **Speak clearly:** Helps transcription accuracy
3. **Background mode:** Claude can listen while you work on other tasks
4. **Batch questions:** Ask multiple questions in one utterance

## Future Enhancements

When Phase 2-4 are complete:
- Streaming mode (interrupt mid-response)
- Voice commands for common tasks
- Custom wake words ("Hey Claude")
- Multi-speaker diarization (group conversations)
