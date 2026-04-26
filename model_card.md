# Model Card — PawPal+ AI Advisor

## What this is

PawPal+ started in Module 2 as a pure scheduling tool — you put in your pets, your tasks, and your available time, and it builds a priority-sorted daily plan. That version had no AI in it at all. Just Python logic, dataclasses, and a Streamlit UI.

For the final project I extended it to include an AI advisor powered by Claude. You pick a pet, click "Analyse Schedule," and the system pulls relevant care knowledge from a local document collection, evaluates your current schedule for gaps and conflicts, then asks Claude to generate specific recommendations for that pet. The whole thing runs through a 5-step pipeline with visible reasoning steps so you can actually see how it got to its answer, not just what the answer was.

---

## Limitations and biases

**The retrieval is keyword-based, which means it misses synonyms.** If you type "feline" anywhere in the app, the retrieval won't match the cats.md document because that document uses "cat" throughout. I knew this trade-off going in. Keyword matching doesn't need any extra services or API calls — you can clone the repo and run it offline immediately. But the downside is real: if your pet's special needs use different words than what's in the documents, retrieval comes back empty or pulls something irrelevant.

**Claude can make up specific numbers.** Even with the knowledge base as context, Claude will sometimes say things like "your dog needs exactly 45 minutes of exercise." That number might be invented. The knowledge base says "30–60 minutes" but Claude picks a specific value instead of a range. I haven't found a clean way to stop this without post-processing every response, so right now the app shows the output and trusts the user to think critically about it.

**The confidence score doesn't actually measure advice quality.** It measures input quality — how much relevant knowledge was retrieved, whether there were schedule conflicts, whether the pet has special needs. A dog with a clean schedule and no special needs will score 0.8 even if Claude gives mediocre advice. A senior cat with thyroid medication will score 0.5 even if Claude gives genuinely useful advice. The score is a signal, not a grade.

**The knowledge base only covers dogs and cats.** If you add a rabbit or a parrot, retrieval falls back to the general.md document, which isn't specific enough to be very useful. The recommendations still get generated but they'll be generic.

---

## Could this be misused?

The biggest risk is someone treating the AI output as veterinary advice. The app calls it an "AI advisor" and Claude writes confidently, so the recommendations can sound more authoritative than they are. Someone managing a pet with a serious condition — diabetes, heart failure, cancer — could follow a recommendation without checking with their vet first and make the wrong call.

I added a sidebar note that says the AI is not a vet, but that's easy to miss. What would actually help is a visible disclaimer directly above every recommendation output, something like "This is not veterinary advice. Confirm with your vet before changing your pet's care plan." I didn't add that in this version and it's probably the most important missing safeguard.

The task suggestion feature could also conflict with an existing vet plan. If a pet is on restricted exercise after surgery, the AI doesn't know that unless you put it in the special needs field. It would still recommend exercise tasks because that's what the knowledge base says dogs need.

---

## What surprised me during testing

**Claude paraphrases differently than I expected.** My puppy test (AG004) checked whether the word "socialization" appeared in Claude's output, because it's in the knowledge base. Claude kept writing things like "expose your puppy to new environments and people" instead — same concept, different words. I had to change the test to check for the partial string "socializ" to catch both "socialize" and "socialization." That was a useful reminder that you can't test generative output the same way you test deterministic logic.

**The confidence score needed more tuning than I expected.** My original version subtracted 0.1 for every conflict detected with no cap. So a schedule with three conflicts dropped the score by 0.3 on top of the special-needs penalty. A senior cat with thyroid medication and two scheduling conflicts was scoring 0.1, which felt too low — the retrieval was still good and the schedule was actually manageable. I added a cap at -0.2 total for conflicts, which made the behavior feel more fair.

**Keyword retrieval worked better than I thought it would.** "Cat thyroid medication senior" reliably pulled cats.md and medical.md on every run. I expected more edge cases to fail, especially with shorter or vague queries, but the scoring handled them well enough. The real gaps were only with exotic pet queries and synonym mismatches.

---

## AI collaboration

**One helpful suggestion:**

When I was building the confidence score, I had subtracted 0.1 per conflict with no upper bound. I asked Claude to review the heuristic and it pointed out that pet owners managing multiple pets might have legitimate conflicts they're already aware of and working around — penalizing them without a cap felt too punishing for normal multi-pet situations. It suggested capping the conflict penalty at -0.2 total. I went with that and it made the score behavior much more consistent across different schedules.

**One flawed suggestion:**

Early on I described what I was building and Claude recommended using a vector database — ChromaDB or Pinecone — with embedding-based similarity search instead of keyword matching. Technically it would give better retrieval. But it would've meant running an embedding model locally or adding a second API call just for retrieval, setting up a persistent database, and handling first-run initialization. For four markdown documents, that's a lot of infrastructure for a marginal gain.

I pushed back and asked Claude to help me think through the setup complexity versus the retrieval improvement. We went through what it would actually take to get ChromaDB running, what could go wrong for someone installing fresh, and whether the retrieval accuracy gain was worth it at this knowledge base size. We both landed on keeping keyword matching. The suggestion wasn't wrong in principle — it just didn't fit the project. That was a good example of where I had to slow down and think through the trade-off instead of just accepting the recommendation.

---

## What I learned

The visible reasoning steps aren't just a UI detail — they're what makes the AI feel trustworthy. When you can see "Step 2: retrieved 4 passages from dogs.md and general.md," you can judge whether the retrieval made sense. When you can see "Step 3: 2 conflicts detected," you know the system accounted for those before generating advice. Without that transparency it's just a black box giving you text.

Confidence scores take real tuning to feel right. I thought it would be a one-line heuristic and it ended up needing several rounds of adjustment to produce numbers that matched my intuition about which situations were actually uncertain. That's a good lesson about evaluation design: you don't know if your metric is working until you test it on cases where you already know what the answer should feel like.
