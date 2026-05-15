# Triage — 3-minute demo video script

Hackathon: Google Cloud Rapid Agent Hackathon (Dynatrace track).
Hard cap: **3:00** — anything past three minutes is not evaluated. Aim for
~2:55, allowing yourself a five-second cushion.

## Heads up — clean the dashboard before recording

If you visit `http://localhost:3000` right now you may see a stack of
already-resolved incidents with timestamps like "Detected 5m ago / 16m ago /
33m ago / 47m ago". Those are real — they're the test runs we did while
debugging the agent earlier. Each click of Seed Demo Incident creates one
record, and they persist in the in-memory store until you wipe them.

For the video, **start from an empty page**. Judges shouldn't see four
identical entries piled up before you've even pressed record. Wipe them with:

```powershell
Invoke-RestMethod -Method POST http://localhost:8080/demo/reset
```

Then refresh the browser. The home page should now show the empty state:
*"No incidents yet. Click Seed demo incident in the header to trigger the
bundled bad-deploy scenario."* That's your opening shot.

---

## Voiceover script — solo builder voice

Read it the way you'd explain your project to a friend who's a developer.
Slightly faster than your normal conversational pace, but natural. About 150
words per minute fits comfortably in three minutes with breathing room for
the on-screen action.

---

**[0:00–0:08] Opening — on the empty incidents page**

> "Hey. I'm a solo builder, and this is **Triage** — my submission to the
> Google Cloud Rapid Agent Hackathon, Dynatrace track. Let me show you what
> it does."

---

**[0:08–0:32] The problem — keep dashboard visible, don't click yet**

> "Every production incident starts the same way. Someone gets paged at 2am,
> opens their laptop, and spends the first ten minutes doing the same
> mechanical work. Read the alert. Pull the traces. Check recent deploys.
> Form a hypothesis. It's high-stakes work, but it's low-creativity work.
> And that's exactly the kind of thing an agent should do. So I built one."

---

**[0:32–0:42] Seed the incident — click Seed Demo Incident in the header**

> "Watch this. I'll trigger a synthetic Dynatrace problem — a failure rate
> spike on a fictional checkout service."
>
> *(Click **Seed demo incident**. Page navigates to `/incidents/<uuid>`.)*

---

**[0:42–1:18] Investigation phase — let the timeline fill in, narrate over it**

> "The agent kicks off immediately. It calls the Dynatrace MCP server to
> pull the problem record, the affected service and its metrics, recent
> failed traces — and look at that, there's a TypeError inside
> calculateTotals — and finally the most recent deployment, version four
> point two point zero, which landed right when the failure rate started
> spiking. Five tool calls, all real, narrated on the timeline."

---

**[1:18–1:48] The plan — point the cursor at the hypothesis + action cards**

> "Then Gemini takes over and produces a structured plan. Top hypothesis at
> ninety percent confidence: a regression in the v4.2.0 deployment of
> checkout. One proposed action — roll back to v4.1.9 — tagged low risk and
> reversible. Notice nothing has touched production yet. Every action stays
> human-gated. The agent does the boring work; I keep the judgment."

---

**[1:48–1:58] Approve — click "Approve & execute"**

> "One click."
>
> *(Click **Approve & execute**. Status flips to Executing.)*

---

**[1:58–2:24] Recovery — watch the status transitions in the badge**

> "The agent fires the rollback through the Dynatrace MCP, polls service
> metrics, and confirms recovery. Executing... Verifying... Resolved.
> Failure rate dropped from 18 percent back to baseline."

---

**[2:24–2:50] Postmortem — scroll down to show the Postmortem card**

> "And Gemini writes the postmortem itself. What happened. The full
> timeline. The root cause, cited from the evidence. The resolution, with
> the exact metric numbers. And three concrete action items I can ticket up
> Monday morning. The entire arc — detection to closed incident — under
> thirty seconds of my attention."

---

**[2:50–3:00] Outro — close on the resolved badge or a still of the dashboard**

> "That's Triage. Built solo, on Gemini, Google Cloud Agent Builder, and
> the Dynatrace MCP server. Source on GitHub — link below. Thanks."

---

Word count: roughly 380 words. At a natural pace of 130–140 wpm with pauses
for the on-screen action, that lands around 2:55–3:00. A few seconds over
three minutes is fine — judges evaluate the first three.

---

## Pre-recording checklist

- [ ] Backend (`uvicorn app.main:app --reload --port 8080`) is running, log
      shows `triage.ready` and `"model": "gemini-2.5-flash"`
- [ ] Frontend (`npm run dev`) is running, home page loads cleanly
- [ ] **`Invoke-RestMethod -Method POST http://localhost:8080/demo/reset`**
      — wipe the four stale resolved incidents
- [ ] Refresh `http://localhost:3000` — page should show the empty state
- [ ] One pre-test seed: click Seed Demo, wait for the plan, click Approve,
      confirm the postmortem renders, then reset again
- [ ] Browser: Ctrl+Shift+B to hide the bookmarks bar
- [ ] Browser: close every tab except `http://localhost:3000`
- [ ] Browser: fresh window or InPrivate so no profile/email shows
- [ ] Browser: Ctrl+0 to reset zoom to 100%
- [ ] Windows: Focus Assist on (Win+N → Focus) — no notifications mid-take
- [ ] Mute Slack / Discord / Teams / email
- [ ] Laptop plugged in (power-saving throttles mic and frame rate)
- [ ] Quiet room, sit close enough to the mic that your voice is clear
- [ ] Do one 10-second test recording, play it back, confirm voice is sharp

## Recording tool — pick one

| Tool | When to pick |
|---|---|
| **OBS Studio** (recommended) | Free, professional. 1080p / 30fps, MP4. Install once, set up once, never lets you down. Use a **Window Capture** source pointing at your Edge window. |
| **Windows Game Bar** (Win+G) | Built-in, zero install. Captures the focused window straight to `Videos/Captures/`. Output is good enough if you're in a hurry. |
| **Loom** | Browser-extension easy. Free tier may add a watermark — check current limits. |

### OBS quick setup (one-time, 10 min)

1. Download from <https://obsproject.com/>
2. Run auto-config wizard — pick "Optimize for recording"
3. Settings → Output → Recording → Recording Format = MP4, Quality = High
4. Settings → Video → Base & Output Resolution = 1920×1080, FPS = 30
5. Sources → + → **Window Capture** → pick your Edge window
6. Mixer → speak a sentence, confirm the Mic level meter is green
7. Hit Start Recording → speak one sentence → Stop Recording
8. Open the MP4 in `Videos/` and confirm both audio and video look clean

## Recording strategy — two options

**One-take (recommended):** Speak the script while clicking through. Allow
2–3 takes. Don't aim for perfect; aim for honest. Take #2 is almost always
your keeper. If you stumble mid-take, **keep going** — finish the take and
trim later. Restarting from a cold setup costs ten times more energy than
letting one weak section happen.

**Two-pass (cleaner):** Record the screen with no voice first, capturing the
demo flow at the right pace. Then record a voiceover in a second pass and
layer it over the screen capture in any free editor (Clipchamp on Windows
works fine). Higher production value but takes longer.

## Exact cursor choreography

1. Reset incidents → refresh browser → home page shows empty state.
2. Start recording.
3. Pause one beat on the empty home page.
4. Read the **[0:00–0:08]** opening + **[0:08–0:32]** problem framing while
   the empty home page sits on screen. Don't move the mouse.
5. Read the **[0:32–0:42]** line and click **Seed demo incident** in the header.
6. Page navigates. Read the **[0:42–1:18]** investigation lines while the
   timeline fills in on the right. Use the mouse to gently track which
   timeline entry you're referring to. Don't click anything yet.
7. When status flips to **Awaiting approval**, read **[1:18–1:48]** and
   slowly scroll so the hypothesis + action cards stay visible.
8. Say "one click" and click **Approve & execute**.
9. Status flips. Read **[1:58–2:24]** while it cycles through
   Executing → Verifying → Resolved.
10. Scroll down to the Postmortem card. Read **[2:24–2:50]**.
11. Final shot: stop scrolling, or close on the resolved badge. Read the
    **[2:50–3:00]** outro.
12. Stop recording.

## Common mistakes to avoid

- Don't talk over a still screen for more than 8 seconds. Always have
  something happening visually.
- Don't read in a flat monotone. The voice you'd use explaining your code
  to a colleague is right.
- Don't click frantically. Give the dashboard a half-second beat between
  meaningful clicks.
- Don't show the backend terminal — the API key is in your environment
  and the terminal output may show paths or names you don't want recorded.
- Don't show your email, profile photo, or any other personal info. Use a
  fresh Edge window.

## Post-recording

1. Trim the start and end with any free editor — Clipchamp (built into
   Windows 11) or the Photos app's video trim both work.
2. Confirm total length ≤ 3:00. If it's 3:05 or so, you can ship it —
   judges only evaluate the first three minutes — but tighter is better.
3. Upload to YouTube:
   - **Visibility: Unlisted** (only viewable with the link)
   - **Title:** `Triage — AIOps Agent | Google Cloud Rapid Agent Hackathon (Dynatrace Track)`
   - **Description:** "Triage is an autonomous on-call SRE agent — my solo
     submission to the Google Cloud Rapid Agent Hackathon (Dynatrace
     track). Built on Gemini, Google Cloud Agent Builder, and the Dynatrace
     MCP server. GitHub: `[paste repo URL]` · Live demo: `[paste hosted URL]`"
   - **Audience:** "No, it's not made for kids"
4. Once YouTube finishes processing, copy the share URL.
5. Paste that URL into the Devpost submission's **Video demo link** field.

## If a take goes wrong mid-record

Don't stop. Finish the take. Edits are cheap; restarting from a cold setup
costs ten times more. You'll see your own raw takes; the judges only see
one cut.
