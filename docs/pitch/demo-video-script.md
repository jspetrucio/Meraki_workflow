# CNL (Cisco Neural Language) - Video Demo Script

> **Type:** 3-Minute Executive Demo Video
> **Presenter:** jspetrucio
> **Audience:** Cisco Leadership
> **Date:** 2026-02-08
> **Goal:** Secure funding to advance CNL from prototype to pilot phase

---

## Script Overview

This is a carefully choreographed 3-minute demo that shows CNL's unique value proposition: natural language network management with BYOK (Bring Your Own Key) AI, combining read operations, write operations with safety confirmations, and competitive differentiation.

**Total Runtime:** 3:00 (180 seconds)

---

## [0:00 - 0:20] INTRO

**VISUAL:**
- Title card: "CNL - Cisco Neural Language"
- Subtitle: "Natural Language Network Management"
- Your name and role

**NARRATION:**
```
Hi, I'm Jose Petrucio, and I'm going to show you how Cisco Neural Language
transforms Meraki network management. Instead of clicking through fifteen
Dashboard screens to configure a network, you simply tell your network
what you want in plain English. Let me show you.
```

**ACTION:**
- Hold on title card for first 10 seconds
- Fade to browser at 0:10

**TIMING NOTE:** Speak at moderate pace. This should fill exactly 20 seconds.

---

## [0:20 - 0:45] OPEN THE APP

**VISUAL:**
- Browser opens to `http://localhost:5173`
- Show the CNL chat interface: clean, modern UI with sidebar, chat area, and input box
- Cursor briefly hovers over the interface elements

**NARRATION:**
```
This is CNL running locally. Clean interface, simple chat experience.
But behind it, there's a multi-agent AI system connected directly to
the Meraki API. Watch what happens when I ask a diagnostic question.
```

**ACTION:**
- Open browser (already should be running in background)
- Show the empty chat interface
- Let the viewer see the layout for 3-5 seconds

**TIMING NOTE:** Pause briefly after "Meraki API" to let the viewer absorb the interface.

---

## [0:45 - 1:15] DEMO 1: Discovery (Read Operation)

**VISUAL:**
- Type in chat: `"Which devices are consuming the most bandwidth on my network?"`
- Press Enter
- Show the message appearing in the chat
- Show the inline status indicator: "Network Analyst working..."
- Show the streaming response building up in real-time
- Final response lists top 5 devices with bandwidth data in a clean table format

**NARRATION:**
```
"Which devices are consuming the most bandwidth on my network?"

CNL classifies this as a network analysis question and routes it to
the Network Analyst agent. The agent fetches real client data from
the Meraki API, interprets the results, and answers in plain English.

No Dashboard navigation. No manual API calls. Just ask and get answers.
```

**ACTION:**
- Type the question
- Wait for response to fully stream in
- Let the final table sit on screen for 2-3 seconds

**TIMING NOTE:**
- Typing should take ~3 seconds
- Response should stream over ~10 seconds
- Narration happens while response is streaming
- Total segment: 30 seconds

**EXPECTED RESPONSE EXAMPLE:**
```
Based on the current client data, here are the top 5 bandwidth consumers:

| Device Name | MAC Address | Usage (GB) | Network |
|-------------|-------------|------------|---------|
| Executive-Laptop | AA:BB:CC... | 45.2 | HQ-Office |
| Conference-TV | DD:EE:FF... | 38.7 | HQ-Office |
| File-Server | GG:HH:II... | 32.1 | Data-Center |
| ...
```

---

## [1:15 - 1:50] DEMO 2: Configuration (Write Operation with Safety)

**VISUAL:**
- Type in chat: `"Block telnet on all switches in the network"`
- Press Enter
- Show the message appearing
- Show inline status: "Meraki Specialist analyzing..."
- **CRITICAL MOMENT:** Show the safety confirmation dialog appearing over the chat:
  - Title: "Configuration Change Requires Confirmation"
  - Risk Level: "MODERATE"
  - Message: "This will modify firewall rules on 12 switches. A backup will be created automatically."
  - Buttons: [Cancel] [Confirm]
- Hover over "Confirm" button
- Click "Confirm"
- Show success response: "Firewall rules updated on 12 switches. Telnet (port 23) blocked. Backup saved to..."

**NARRATION:**
```
Now let's do something more powerful -- a configuration change.

"Block telnet on all switches in the network."

Notice what happens. CNL knows this is a write operation, so the safety
layer kicks in automatically. It requires explicit confirmation before
making any changes. It also creates an automatic backup so we can rollback
if needed. This is network safety by design.
```

**ACTION:**
- Type the command
- Wait for confirmation dialog
- Pause 2 seconds on the dialog to let viewer read it
- Click Confirm
- Wait for success message

**TIMING NOTE:**
- Total segment: 35 seconds
- Pause on confirmation dialog is critical -- viewer must see the safety feature
- Speak slowly during "safety layer kicks in automatically" for emphasis

---

## [1:50 - 2:15] DEMO 3: BYOK Explanation

**VISUAL:**
- Split screen OR simple slide:
  - Left: CNL logo
  - Right: Logos of AI providers: OpenAI, Anthropic Claude, Azure OpenAI, AWS Bedrock, Google Gemini
- OR show Settings panel briefly with "AI Provider" dropdown

**NARRATION:**
```
Here's what makes CNL unique in the industry: Bring Your Own Key.

The customer uses their OWN AI provider. OpenAI, Claude, Azure,
AWS Bedrock, Google -- whatever your enterprise already has approved
and budgeted for.

Your network data never leaves your infrastructure. No vendor lock-in.
No additional AI subscription from Cisco.

CNL is the ONLY natural language network tool that offers this level
of customer control.
```

**ACTION:**
- Show the visual for 15 seconds
- OR briefly open Settings > AI Provider to show the dropdown with multiple options

**TIMING NOTE:**
- Emphasize "ONLY natural language network tool" with slight voice emphasis
- This is the key differentiator -- make it memorable

---

## [2:15 - 2:40] COMPETITIVE POSITIONING

**VISUAL:**
- Comparison table slide (simple, clean design):

```
| Capability              | Marvis | ThousandEyes | CNL     |
|-------------------------|--------|--------------|---------|
| NL Diagnostics          | ✓      | ✓            | ✓       |
| NL Configuration        | ✗      | ✗            | ✓       |
| BYOK (Any AI Provider)  | ✗      | ✗            | ✓       |
| Security Audits         | ✗      | ✗            | ✓       |
| Auto-Remediation        | Partial| ✗            | ✓       |
```

**NARRATION:**
```
Let's talk competition.

Juniper Marvis can diagnose network issues, but it can't configure anything.
ThousandEyes AI Assistant monitors beautifully, but it doesn't change anything.

CNL does both. Discovery, configuration, automation, security audits --
all through natural language. And with Bring Your Own Key, we're the only
solution that gives customers full control over their AI and their data.
```

**ACTION:**
- Display the comparison table
- Table should be visible for full 25 seconds
- Simple animation: checkmarks appear one by one as you mention each capability

**TIMING NOTE:**
- Speak deliberately -- this is the strategic "why this matters" moment
- Pause briefly after "ThousandEyes... doesn't change anything" for impact

---

## [2:40 - 2:55] THE NUMBERS

**VISUAL:**
- Simple slide with key business metrics (large, readable fonts):

```
CUSTOMER ROI
• $725K saved per year (5-engineer team, 50 sites)
• 350-600% return on investment
• 2-3 month payback period

CISCO OPPORTUNITY
• $212M - $451M annual revenue potential
• $1.6M development investment
• 13,150% ROI in Year 1
• Payback in < 1 month
```

**NARRATION:**
```
The business case is compelling.

A team of five engineers managing fifty sites saves over seven hundred
thousand dollars per year. That's a three-hundred-fifty to six-hundred
percent ROI for the customer.

For Cisco, this represents a two-hundred-million-dollar-plus annual
revenue opportunity with less than two million in development investment.
That's a thirteen-thousand-percent return in year one.

The prototype you just saw has six hundred forty-six passing tests and
is ready for pilot.
```

**ACTION:**
- Display the numbers slide
- Keep it visible for the full 15 seconds

**TIMING NOTE:**
- Pronounce numbers clearly: "seven hundred thousand" not "700K"
- Slight emphasis on "six hundred forty-six passing tests" -- this shows maturity
- Speak with confidence but not arrogance

---

## [2:55 - 3:05] CLOSING

**VISUAL:**
- Return to CNL chat interface OR closing title card with:
  - "CNL - Cisco Neural Language"
  - "Demo available on request"
  - "Contact: jspetrucio@cisco.com" (or appropriate contact)
  - Cisco logo

**NARRATION:**
```
This is what Meraki sounds like.

Thank you.
```

**ACTION:**
- Hold on closing card for 5 seconds
- Fade to black at 3:05

**TIMING NOTE:**
- "This is what Meraki sounds like" should land with impact
- Pause 1 second before "Thank you"
- Keep it short and memorable

---

## Pre-Recording Checklist

Run through this checklist 30 minutes before recording:

### Backend & Frontend
- [ ] Backend running: `source venv/bin/activate && python -m uvicorn scripts.server:app --host 0.0.0.0 --port 3141 --reload`
- [ ] Verify backend: `curl http://localhost:3141/health` → should return `{"status":"ok"}`
- [ ] Frontend running: `cd frontend && npx vite --host`
- [ ] Verify frontend: Open `http://localhost:5173` → should load CNL interface
- [ ] WebSocket connection active (check browser console for "WebSocket connected")

### Meraki Connection
- [ ] `.env` file exists with valid `MERAKI_API_KEY` and `MERAKI_ORG_ID`
- [ ] Test API: `curl -H "X-Cisco-Meraki-API-Key: YOUR_KEY" https://api.meraki.com/api/v1/organizations/YOUR_ORG_ID/networks`
- [ ] Verify organization has real data: networks, devices, clients
- [ ] Ensure at least 10-15 active clients for bandwidth demo
- [ ] Ensure at least 5+ switches for firewall demo

### LLM Provider (BYOK)
- [ ] AI provider configured (OpenAI, Claude, etc.)
- [ ] API key valid and has credits/quota
- [ ] Test classification: send a test message in chat → should get response
- [ ] Streaming works (response appears word-by-word, not all at once)

### Demo Commands (Test Each One)
1. [ ] Test discovery command: `"Which devices are consuming the most bandwidth?"`
   - Should return table with real device names
   - Should complete in < 10 seconds
2. [ ] Test config command: `"Block telnet on all switches"`
   - Should show confirmation dialog
   - Should NOT execute until you click Confirm
   - After confirm, should show success message

### Recording Environment
- [ ] Close all unnecessary browser tabs (only keep CNL tab open)
- [ ] Close email, Slack, notifications (enable Do Not Disturb mode)
- [ ] Browser zoom at 100% (Cmd+0 on Mac, Ctrl+0 on Windows)
- [ ] Browser theme: clean, professional (light or dark -- pick one and stick with it)
- [ ] Desktop wallpaper: professional or blank
- [ ] Hide desktop icons (Mac: `defaults write com.apple.finder CreateDesktop false && killall Finder`)
- [ ] Hide bookmarks bar in browser

### Screen Recording Setup
- [ ] Screen resolution: 1920x1080 (1080p)
- [ ] Recording tool ready: QuickTime (Mac), OBS Studio, or Loom
- [ ] Test 10-second recording → play back to verify quality
- [ ] Audio input: built-in mic or external mic (test levels, no clipping)
- [ ] No background noise (close windows, turn off fans)
- [ ] Test recording: speak into mic → playback → adjust levels if needed

### Visual Slides Preparation
- [ ] BYOK slide ready (logos of AI providers)
- [ ] Competitive comparison table ready
- [ ] Business numbers slide ready
- [ ] Closing card ready
- [ ] All slides exported as images or in a separate browser tab ready to switch to

### Final Test Run
- [ ] Do a complete practice run (3 minutes)
- [ ] Time yourself with a stopwatch
- [ ] Verify all three demos work end-to-end
- [ ] Adjust speaking pace if too fast/slow
- [ ] If any step fails, STOP and fix before recording

---

## Backup Plan (If Things Go Wrong)

### If API is Slow
- **Problem:** Meraki API takes >10 seconds to respond
- **Solution:** Have a pre-recorded screen capture of the response ready to insert in post-production
- **Prevention:** Test API speed before recording; if slow, wait 5 minutes and retry

### If LLM Response is Unexpected
- **Problem:** AI generates a weird or unhelpful response
- **Solution:** Re-run the demo (mention casually: "AI responses vary, let me try that again")
- **Prevention:** Test each command 3 times before recording to ensure consistent responses

### If Frontend Crashes
- **Symptoms:** White screen, "Cannot connect to server", blank chat
- **Solution:**
  ```bash
  pkill -f vite
  cd frontend
  npx vite --host
  # Wait 10 seconds, reload browser
  ```
- **Prevention:** Don't run other heavy processes during recording

### If Backend Crashes
- **Symptoms:** "500 Internal Server Error", no response, WebSocket disconnect
- **Solution:**
  ```bash
  pkill -f uvicorn
  source venv/bin/activate
  python -m uvicorn scripts.server:app --host 0.0.0.0 --port 3141 --reload
  # Wait 5 seconds, reload browser
  ```
- **Prevention:** Don't touch backend code during recording

### If Confirmation Dialog Doesn't Appear
- **Problem:** Config command executes immediately without confirmation
- **Likely Cause:** Safety layer disabled or misconfigured
- **Solution:** Check `scripts/safety.py` → `SAFETY_ENABLED = True`
- **Workaround:** Mention safety feature verbally, show settings panel where safety is enabled

### If Recording Audio Has Echo
- **Problem:** Hear your own voice doubled or delayed
- **Solution:** Use headphones to prevent speaker feedback into mic
- **Prevention:** Always test with headphones before final recording

---

## Tips for Recording

### Voice & Delivery
- **Speak slowly and clearly** -- aim for 130-150 words per minute (conversational)
- **Pause briefly** after key points to let them land (e.g., after "BYOK", after "only solution")
- **Vary your tone** -- don't be monotone (show enthusiasm for impressive features)
- **Don't narrate what you're typing** -- let the viewer read the command as you type
- **Practice the "money lines"** several times:
  - "This is network safety by design."
  - "CNL is the ONLY natural language network tool that offers this."
  - "This is what Meraki sounds like."

### Mouse & Typing
- **Keep mouse movements smooth** -- no jerky cursor motion
- **Type at moderate speed** -- not too fast (viewers can't read), not too slow (wastes time)
- **Don't correct typos** -- if you make one, just delete and retype smoothly (or start over)
- **Use natural pauses** -- let responses fully appear before moving to the next section

### Timing Management
- **Practice at least 3 times** before the final recording
- **Time each section** with a stopwatch:
  - Intro: 20 seconds
  - Open App: 25 seconds
  - Demo 1: 30 seconds
  - Demo 2: 35 seconds
  - BYOK: 25 seconds
  - Competitive: 25 seconds
  - Numbers: 15 seconds
  - Closing: 10 seconds
  - **Total: 3:05** (allows 5 seconds buffer)
- **If running over time:** Cut words from narration, NOT features from the demo
- **If running under time:** Add 1-2 second pauses, don't rush to fill time

### Energy & Presence
- **Smile while speaking** -- it changes your voice tone (sounds more confident)
- **Sit up straight** -- better posture = better voice projection
- **Imagine you're presenting to a room** -- not just reading a script
- **First take is rarely the best** -- plan for 3-5 recording attempts

### Post-Recording
- **Watch the full recording immediately** before stopping the recording session
- **Check for:**
  - Audio quality (no background noise, clear voice)
  - Video quality (smooth, no lag, readable text)
  - All demos worked as expected
  - No awkward pauses or "um"s
  - Timing is within 3:00 - 3:10
- **If anything is off:** Re-record immediately (while everything is still set up)

---

## What NOT to Do

1. **Don't apologize** -- no "sorry" or "oops" or "let me try that again" (just re-record)
2. **Don't say "um" or "uh"** -- pause silently instead
3. **Don't rush** -- speaking too fast makes you sound nervous
4. **Don't over-explain** -- trust the demo to show the value
5. **Don't mention what you're NOT showing** -- focus only on what IS working
6. **Don't say "only a prototype"** -- say "ready for pilot" (positive framing)
7. **Don't read the script robotically** -- speak naturally, conversationally

---

## Script Variations (Optional)

### If You Have More Time (5-minute version)
- Add a 4th demo: "Create a workflow to alert me when a device goes offline for 10 minutes"
- Add a security audit demo: "Check my network for insecure SSIDs"
- Show the Settings panel with AI provider selection

### If You Have Less Time (2-minute version)
- Cut the competitive positioning section
- Cut the BYOK explanation (just mention it briefly in intro)
- Keep only Demo 1 (read) and Demo 2 (write)

### For a Technical Audience (Engineers)
- Show more of the agent router decision-making
- Show the WebSocket streaming in browser DevTools
- Mention the 646 passing tests earlier
- Show the CLI version (`meraki discover full`)

### For a Business Audience (Executives)
- Lead with the numbers slide instead of ending with it
- Shorten the technical demos (less time watching responses stream)
- Add more competitive positioning (why this beats Marvis)
- Emphasize the $200M+ revenue opportunity

---

## Success Metrics for This Video

After viewing, the audience should be able to answer:

1. **What is CNL?** → Natural language interface for Meraki network management
2. **What makes it unique?** → BYOK + NL configuration (not just monitoring) + safety layer
3. **How does it beat competitors?** → Marvis can't configure, ThousandEyes can't configure, CNL does both
4. **What's the business case?** → $200M+ revenue opportunity, $1.6M investment, 13,000% ROI
5. **Is it ready?** → Yes, 646 tests passing, ready for pilot

If they can't answer all 5 after watching once, the video failed.

---

## Final Checklist (Day of Recording)

- [ ] I've practiced the full script at least 3 times
- [ ] All backend and frontend services are running
- [ ] I've tested both demo commands and they work
- [ ] My recording environment is clean and professional
- [ ] I've set Do Not Disturb mode on all devices
- [ ] I have water nearby (stay hydrated, clear voice)
- [ ] I'm wearing professional attire (even if off-camera -- affects confidence)
- [ ] I've set a timer for 3:30 as a hard stop
- [ ] I'm ready to record 3-5 takes to get the best one
- [ ] I've closed all unnecessary applications

---

## After Recording

1. **Watch the recording immediately** (before ending the recording session)
2. **Export the video** in 1920x1080 MP4 format (H.264 codec, 30fps)
3. **Backup the raw recording** (keep unedited version)
4. **Optional: Light editing**
   - Trim any silence at start/end
   - Add title card if not recorded
   - Add fade in/out transitions
   - Normalize audio levels
   - Add subtle background music (optional, very low volume)
5. **Share with stakeholders** via secure link (Google Drive, OneDrive, Cisco Webex)
6. **Create a thumbnail image** (CNL logo + "3-Minute Demo")
7. **Write a 2-sentence description** for when you share:
   > "This 3-minute demo shows CNL (Cisco Neural Language), a natural language interface for Meraki network management. See how engineers can discover, configure, and automate networks using conversational commands -- with BYOK AI, automatic safety confirmations, and a $200M+ revenue opportunity for Cisco."

---

## Contact & Support

**Questions about the demo?**
- Technical issues: Check the Backup Plan section above
- Script revisions: Edit this document directly
- Competitive data: See `/docs/business/roi-business-case.md`

**Ready to record?**
✅ Run through the Pre-Recording Checklist
✅ Do a practice run
✅ Hit Record

---

*Good luck with the recording! Remember: confidence, clarity, and conciseness. You've built something remarkable -- now show them why it matters.*

**This is what Meraki sounds like.**
