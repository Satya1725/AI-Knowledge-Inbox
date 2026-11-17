# UI Testing Guide

Sample content to paste into the app, and what you should see. Each section says which tab to use, what goes in **Title**, and what goes in the main box.

---

## 1. Notes

Use the **Note** tab. Paste the text into the big box and the title into the **Title** field.

### Note 1

**Title:** `Project Falcon – Kickoff`

```
Project Falcon kickoff notes

The launch date for Project Falcon is March 14. Priya owns the backend API and Marcus owns the mobile app.
The budget is capped at $40,000 for Q1.

Decisions: we are using PostgreSQL instead of MongoDB because we need strong consistency for payments.
The weekly sync is every Tuesday at 11am in the Orion meeting room.

Risks: the payment provider's sandbox is unstable, and the design team is two weeks behind on the onboarding screens.
```

### Note 2

**Title:** `Team Onboarding Checklist`

```
New joiners should complete these in their first week:

- Get a laptop from IT (ask for Ravi on the 3rd floor).
- Request GitHub and AWS access through the #access-requests Slack channel.
- Read the engineering handbook in Notion.
- Set up the local dev environment using the "make bootstrap" command.

The buddy for every new engineer is assigned by Ananya. Probation lasts 90 days.
Leave requests go through the HR portal and need two days' notice.
```

### Note 3

**Title:** *(leave empty to test the auto-title)*

```
Book recommendations from Sarah

Deep Work by Cal Newport – about focusing without distraction.
Atomic Habits by James Clear – small habits compound over time.
The Pragmatic Programmer – classic advice for software engineers.

Sarah said to start with Atomic Habits because it is the easiest read.
```

The title should be filled in automatically from the first line: **"Book recommendations from Sarah"**.

### Note 4

**Title:** `Home Wi-Fi & Utilities`

```
Wi-Fi network name: Falcon-Home-5G
The router is in the living room behind the TV.
The internet provider is AirFiber, and the support number is 1800-123-456.
The electricity bill is due on the 5th of every month.
```

---

## 2. URLs

Use the **URL** tab. You can leave **Title** empty, and the page's own title will be used.

| URL | Title to type (optional) | Expect |
|---|---|---|
| https://en.wikipedia.org/wiki/Retrieval-augmented_generation | `RAG – Wikipedia` | Ready, ~40 chunks |
| https://en.wikipedia.org/wiki/Vector_database | *(empty)* | Title becomes "Vector database - Wikipedia" |
| https://paulgraham.com/greatwork.html | `How to Do Great Work` | Ready, ~110 chunks. Large page, so it takes a few seconds |
| https://example.com | *(empty)* | Ready, 1 chunk. Tiny page |

---

## 3. Questions to ask

Type these into **Ask your inbox**.

### Answered from notes

| Question | Expected answer contains |
|---|---|
| When is Project Falcon launching and who owns the backend? | March 14, Priya |
| Why did the team choose PostgreSQL? | Strong consistency for payments |
| What are the risks for Project Falcon? | Unstable payment sandbox, design two weeks behind |
| When is the weekly sync and where? | Tuesday 11am, Orion room |
| What should a new engineer do in their first week? | Laptop, GitHub/AWS access, handbook, `make bootstrap` |
| Who assigns the buddy for new engineers? | Ananya |
| Which book should I read first? | Atomic Habits |
| What is my Wi-Fi network name? | Falcon-Home-5G |

### Answered from URLs

| Question | Expected |
|---|---|
| What problem does retrieval-augmented generation solve? | Cites the RAG Wikipedia page |
| How do vector databases find similar items? | Mentions nearest neighbour / similarity search |
| What does Paul Graham say about curiosity? | Cites "How to Do Great Work" |

### Across several sources

| Question | Expected |
|---|---|
| Summarize everything I've saved | Cites several different sources |
| What deadlines or dates do I have in my notes? | March 14, Tuesday sync, bill on the 5th |

### Not in your content (the app should not make up an answer)

| Question | Expected |
|---|---|
| What is the capital of France? | "I couldn't find that in your saved content" |
| What is Marcus's phone number? | Says it isn't in your saved content |

---

## 4. Notifications & loading states

| Action | What you should see |
|---|---|
| Click **Save note** | Button shows a spinner and **"Saving…"** |
| Save succeeds | Toast: **"Note saved to Library"**, "Indexing it now…". The card appears with a moving purple bar and an **Indexing** badge |
| Indexing finishes | Toast: **"'Project Falcon – Kickoff' is ready"**, "Indexed into N chunks…". Badge turns green **Ready** |
| Save a URL | Toast: **"URL saved to Library"**. The card says "Fetching page & embedding…" |
| Delete an item (hover the card, then click the trash icon) | Modal slides in over a blurred background, showing the item's title and chunk count. **Cancel**, **Esc** or clicking outside closes it smoothly. **Delete** shows "Deleting…", then the modal closes and a toast says **"Item deleted"** |
| Ask a question | Bouncing dots, with steps that change: "Understanding your question" → "Searching your saved content" → "Writing an answer with Gemini". Then the answer fades in |
| Refresh the page | Grey skeleton cards appear briefly while the Library loads |

---

## 5. Error cases

| Try this | Expected |
|---|---|
| URL: `https://httpbin.org/status/404` | Error toast: **"Couldn't index…"**, "The site responded with HTTP 404." Card shows a red **Failed** badge |
| URL: `https://this-domain-does-not-exist-12345.com` | Failed: "Could not reach the URL…" |
| URL: `https://httpbin.org/image/png` (an image, not a page) | Failed: "Unsupported content type 'image/png'…" |
| Note with only spaces | Save button stays disabled |
| Question with fewer than 3 characters | Ask button stays disabled |
| Stop the backend, then save a note | Red message: "Can't reach the server. Is the backend running on port 8000?" |
| Click a citation chip like **[1]** in an answer | Scrolls to that source and highlights it |
