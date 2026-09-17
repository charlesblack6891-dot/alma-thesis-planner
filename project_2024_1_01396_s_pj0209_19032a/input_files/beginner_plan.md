## 1. The Goal

Imagine you're looking at a distant city at night from an airplane. From far enough away, the whole city is just one blob of light. You can measure how bright it is, but you can't tell whether that brightness comes from one blazing stadium in the middle or from a million evenly-spread streetlights. Those two cities would look identical from a distance — but they are completely different places.

That is the situation astronomers are in with a galaxy called **PJ0209**. It's a galaxy so far away that its light has been traveling toward us for roughly 10 billion years, so we're seeing it as it was when the universe was young. Back then, galaxies were forming stars at furious rates — this one is a "starburst," a galaxy building new stars hundreds or thousands of times faster than our own Milky Way does today. Stars form out of cold gas clouds, so if you want to understand *why* this galaxy is forming stars so fast, you need to understand the gas.

Here's the lucky break that makes this project possible. Between us and PJ0209 there happens to be another massive object (a galaxy or cluster of galaxies). Its gravity bends the light passing by it, exactly the way a glass lens bends light — this is called **gravitational lensing**. The result is that PJ0209 appears both much brighter *and* much bigger on the sky than it really is: nature has handed us a free zoom lens. Instead of a single unresolved dot, we can actually see structure inside the galaxy. Lensed images usually look smeared into arcs or split into several copies of the same object, like a reflection in a funhouse mirror.

Now, how do you measure gas you can't see? Cold gas is mostly hydrogen molecules, which are essentially invisible. But mixed into that gas is a small amount of **carbon monoxide (CO)** — the same molecule as in car exhaust — and CO glows at very specific radio frequencies. A CO molecule can spin, and it can only spin at certain fixed rates, labeled J = 1, 2, 3, ... 15 and so on. When it drops from one spin rate to the next one down, it emits radio light at one exact frequency. Each of those is a separate "line" we can observe. The crucial fact: **it takes hotter, denser gas to make a molecule spin fast.** So the low-J lines (slow spin) come from everywhere in the galaxy, including cool diffuse gas, while the high-J lines (fast spin) only come from the hottest, densest, most compressed regions.

That gives you a thermometer-and-pressure-gauge in one. If you take the brightness of a high-J line and divide it by the brightness of a low-J line, you get a **line ratio**, and that ratio tells you about the physical conditions of the gas — how hot and how dense it is. Previous work has already measured that ratio for PJ0209 *as a whole*, one number for the entire galaxy. Your project asks the next question:

> **Is that single global number telling the truth about the whole galaxy, or is it an average that hides something?**

Concretely: is the gas in PJ0209 in roughly the same physical state everywhere, or is there a small, extremely hot and dense "engine" buried in the middle of a much larger, cooler, calmer reservoir of gas? Those two pictures give the same galaxy-wide average but mean very different things about how the galaxy is building stars.

The elegant part — and the reason this is doable by one student in a year rather than by a team over five years — is a trick with the lensing. Gravitational lensing brightens everything at a given spot on the sky by the same factor. If you take *two* CO lines measured **at the same spot** and divide one by the other, that magnification factor appears on the top and bottom of the fraction and **cancels out**. You never have to build a model of the lens, which is the single hardest and most expensive part of studying lensed galaxies. You get physically meaningful information for free, just by dividing. (There's a caveat — if a compact bright region and an extended faint region get magnified by *different* amounts, the cancellation isn't perfect. Measuring how big that effect could be is part of your job, not something you sweep under the rug.)

**What you should actually have at the end:**

1. **A set of matched images ("cubes") of PJ0209**, one for each CO line observed, all processed so carefully that they're genuinely comparable to each other — same resolution, same sensitivity to the same size scales, same pixel grid. This sounds like plumbing. It is the hardest and most important thing you will do, and getting it wrong is how people publish wrong results in this field.
2. **A set of ratio maps** — pictures of the galaxy where the color at each point isn't brightness but the *ratio* of two CO lines, with proper error bars and a clear statement of which parts are trustworthy. Plus plots of "ratio versus distance from the center," which is where the science actually shows up.
3. **A physical answer for ~5–10 hand-picked regions** of the galaxy: what temperature and density is the gas there? Not a single number — realistically, a *region of allowed possibilities* for each spot, shown as a contour plot. Saying honestly "the data pin down the pressure well but can't separate temperature from density" is a legitimate, publishable result, not a failure.
4. **A one-sentence answer to the actual question**: do the different regions of PJ0209 require genuinely different gas conditions, or are they all consistent with the same conditions? Either answer is a real result.
5. **A working, documented, scripted pipeline** that the wider research team can point at the other 7 galaxies in this program. This is a real deliverable people will use, which is unusually satisfying for a first project.

Why should you care? Because you'd be measuring the internal structure of a galaxy that existed when the universe was a fifth of its current age, using a naturally occurring cosmic telescope, and you'd be settling whether the numbers everyone currently quotes for these objects mean what people think they mean. That's a genuinely open question, and the answer fits on one plot that you make.

---

## 2. Skills You'll Need

Be reassured up front: nobody starts a project like this already knowing all of this. The list below is what you'll build *during* the project. What matters is which things you should start touching in week one versus which can wait until month three.

**Python — yes, and it's essential (needed level: comfortable beginner).**
This project is entirely computational. You will not touch a telescope; you'll sit at a computer. You need to be able to: write and run a script, use loops and functions, read and write files, and use `numpy` (arrays of numbers) and `matplotlib` (making plots). You do *not* need to be a software engineer, know object-oriented design, or write fast code.
*How to pick it up:* any introductory Python course aimed at scientists (roughly the first third of a "Python for data science" or "scientific Python" course). Then specifically work through a tutorial on `numpy` arrays and one on `matplotlib`. If you can load a table of numbers and plot two columns against each other, you're ready to start. Budget two weeks of evenings if you're starting cold.

**CASA — the specialized software for radio telescope data (needed level: none at the start; you'll learn it here).**
CASA is the standard program for turning raw ALMA telescope data into images. It's driven by Python, so Python comes first. It has a reputation for being clunky; this is deserved, and it's not your fault when it's confusing.
*How to pick it up:* the official CASA guides include step-by-step worked examples using real ALMA data ("CASA Guides"). Do one of those beginner examples start to finish before touching your own data. Expect to spend a full week on this and to feel lost for the first three days. That's normal.

**How a radio telescope actually makes a picture (needed level: conceptual, not mathematical).**
ALMA isn't one dish; it's ~50 dishes spread over a desert, working together. Combining them mimics one enormous telescope, which is why the images are so sharp. But there's a catch that dominates this whole project: **an array of separated dishes is sensitive to some sizes of structure and blind to others.** Widely separated dishes see fine detail; closely spaced dishes see big smooth structures. If your gaps are in the wrong places, big smooth emission simply vanishes from your image.
Two terms you'll live with:
- **The beam** (or "synthesized beam"): the telescope's blur spot — the smallest thing it can resolve, like the fuzziness of an out-of-focus camera. Quoted as an angle, e.g. 0.15 arcseconds (an arcsecond is 1/3600 of a degree — roughly the width of a coin seen from 4 km away).
- **uv coverage**: the technical bookkeeping of which dish separations you had, and therefore which structure sizes your image is sensitive to.
Here's the thing that makes this concept the heart of your thesis rather than trivia: the high-J and low-J CO lines are at *different radio frequencies*, and a telescope's beam and its size-sensitivity both depend on frequency. So straight out of the box, your high-J image is sharper and blinder-to-big-structures than your low-J image. If you just divide them, you'd see a fake pattern — the ratio rising toward the center — that looks *exactly* like the hot compact core you're hunting for, but is pure instrumental artifact. Most of your first three months is spent forcing all the images to have identical blur and identical size-sensitivity so that this can't happen.
*How to pick it up:* read the introductory chapters of "Interferometry and Synthesis in Radio Astronomy" (skim the math, absorb the pictures), or better, the NRAO Synthesis Imaging Summer School lecture notes, which are written for beginners. Don't try to master it before starting — revisit it after your first hands-on imaging attempt, when the concepts will suddenly click.

**Basic astronomy concepts (needed level: solid intuition, no math).**
You should be comfortable with:
- *What a galaxy is* and that star formation happens in cold gas clouds.
- *Redshift* — because the universe is expanding, light from distant objects is stretched to longer wavelengths. A galaxy at redshift z = 2 has its light stretched by a factor of 3. **This matters practically**: the CO line that a lab emits at 345 GHz arrives at your telescope at a totally different frequency, and you have to compute that yourself for PJ0209 rather than assume it.
- *Flux and brightness* — how much energy arrives per second. You'll mostly work in ratios, which is merciful, because ratios don't require you to get absolute calibration perfect.
- *Gravitational lensing* — described above; conceptual understanding is enough.
- *Spectral lines* — that atoms and molecules emit at specific, known frequencies, and that this frequency is a fingerprint identifying the molecule.
*How to pick it up:* an "Introduction to Astrophysics" survey course or textbook (something like Carroll & Ostlie, or an open-access intro-astronomy text). One or two chapters on the interstellar medium and one on cosmology/redshift covers most of it.

**Some new vocabulary you'll meet constantly:**
- **Spectral line cube**: your main data product. An ordinary image is 2D (a grid of pixels). A cube adds a third axis: frequency, which translates to velocity. So a cube is a stack of images — one image per velocity slice. Think of it as a flipbook where flipping through the pages shows you gas moving at different speeds. This is how you see gas rotating or streaming inside the galaxy.
- **Moment-0 map**: take a cube and add up all the pages of the flipbook into one image. That gives you "total amount of CO emission at each spot" — the map you form ratios from. (Moment-1 is the average velocity at each spot; moment-2 is the spread of velocities.)
- **Continuum**: the smooth background glow from dust, present at all frequencies, as opposed to the sharp spikes from spectral lines. You have to carefully subtract it before measuring lines — and you'll also keep it as its own useful image.
- **Non-LTE / LVG / RADEX**: LTE is a simplifying assumption that gas is in perfect thermal balance; real interstellar gas often isn't, so "non-LTE" means doing it properly. **RADEX** is a small, free program that does this calculation for you: you feed it a temperature, a density, and an amount of CO, and it predicts how bright each CO line would be. You'll run it thousands of times over a grid of guesses and see which guesses reproduce your measured ratios. You do *not* need to understand its internals to use it correctly — you need to understand its inputs and outputs.

**Math (needed level: lower than you fear).**
No calculus is required to do this project. What you actually need: logarithms (because everything spans huge ranges and gets plotted on log axes), and basic error propagation — if A has an uncertainty and B has an uncertainty, what's the uncertainty on A/B? That's one formula you'll look up once and use forever. Later, a working understanding of χ² ("how badly does this model miss the data") and what a *likelihood surface* is (a map showing which combinations of temperature and density are compatible with your measurements). If you eventually use MCMC (a technique for exploring that map efficiently), the `emcee` package's own tutorial is genuinely beginner-friendly.
*How to pick it up:* a short "statistics for physicists" tutorial on error propagation and χ² fitting; the `emcee` docs later on.

**Practical tools (needed level: minimal, learn as you go).**
- **Command line / terminal** — enough to move between folders and run scripts.
- **Git** — version control, so you can undo mistakes and so your pipeline is something others can actually use. Learn five commands (`clone`, `add`, `commit`, `push`, `log`) and stop there for now.
- **FITS files** — the standard astronomy image format; `astropy` reads them in one line.
- **A note on hardware**: ALMA datasets are big (tens to hundreds of GB) and imaging is slow. Find out in week one whether you'll work on your laptop or on a departmental/observatory server. If it's a server, learning to run long jobs remotely is a week-one task, not a week-ten one.

---

## 3. Your First Week

The honest framing: **week one is not about science. It's about being able to open the data and make one picture.** If by Friday you have looked at a real spectrum from PJ0209 and identified one CO line in it, you have had an excellent week. Most students spend week one fighting software installation, and that's a normal, expected experience rather than a sign you're behind.

**Day 1 — Read, and write down what you don't understand.**

Spend the morning reading the proposal abstract and the research idea, slowly, with a blank page next to you. Every time you hit a term you can't explain out loud, write it down. You will end up with 30–40 terms. That list *is* your syllabus.

Then spend the afternoon on just five of them: gravitational lensing, redshift, the CO ladder (why different J lines trace different conditions), what an interferometer beam is, and what a spectral cube is. Wikipedia plus one intro-astronomy chapter each is fine at this stage. Don't try to reach expert-level understanding; aim for "I could explain this to a friend at dinner."

End of day, write down in your own words, in three sentences, what the project is trying to find out. Show it to your advisor. If it's wrong, you've just saved yourself two weeks — this is the cheapest possible time to be corrected.

**Day 2 — Sort out computing, and find out whether the data exist yet.**

Two parallel tasks.

First: install things. Get Python going (use Anaconda or Miniconda — it manages the messy dependencies for you), then install `astropy`, `numpy`, `matplotlib`, and `spectral-cube`. Then install CASA, which is a separate large download. **Expect this to go wrong.** Version conflicts, permission errors, "command not found" — this is where beginners lose two days and conclude they're bad at this. You're not; installation is genuinely the worst part of astronomy software. Ask for help after 45 minutes of being stuck, not after two days. If your department has a shared machine with CASA already set up, use it and skip the pain entirely.

Second, and important: go to the **ALMA Science Archive** website, search for project code **2024.1.01396.S**, and find out what's actually there. Is the data public yet, or still in its proprietary period? Is PJ0209 among the delivered observations? How many spectral setups, how big are the files? Ask your advisor whether you have access rights — if the team is on the proposal, you likely do, but that needs arranging and can take days, so start it now rather than later.

If the answer is "PJ0209 hasn't been delivered yet," don't panic and don't go find a different galaxy. The plan already has a contingency: you build and test the whole analysis on **simulated** data made to match what ALMA will deliver, then switch to the real thing the day it arrives, with your machinery already proven. That's a legitimate and, honestly, a rather smart way to work. It just changes what you do on Days 4–5.

**Day 3 — Do somebody else's tutorial before touching your own data.**

Resist the urge to start on PJ0209. Instead, work all the way through one official CASA Guide beginner tutorial — one that walks you through calibrating and imaging a real ALMA dataset of some unrelated object, start to finish, following instructions exactly.

Yes, this feels like a detour. It isn't. It teaches you what a normal, working session looks like: what commands you type, how long they take, what the output looks like when it's fine. Without that baseline, when your own data misbehaves in week four, you'll have no idea whether what you're seeing is a bug or just how it looks.

Where you'll get stuck: CASA task syntax is fussy and error messages are unhelpful. Keep a running text file — `notes.md` — where you paste every error and what fixed it. In three months this file will be more valuable than any textbook you own.

**Day 4 — Open the actual data and just look at it.**

Now download what's available for PJ0209 (or your simulated stand-in). If real data: get the delivered products and, crucially, the **weblog** — a big folder of automatically generated diagnostic plots and tables from the observatory's own processing. It looks intimidating. Open it anyway and click around; it tells you which antennas were used, what frequencies were observed, and how good the weather was.

Your one concrete goal today: **plot a spectrum.** That is, make a graph with frequency on the x-axis and brightness on the y-axis, showing everything the telescope recorded across each frequency band. In CASA the task is `plotms`; on delivered image cubes you can also do it in Python with `spectral-cube`. You're looking for a bump — a hill rising above the noisy baseline. That bump is a CO line from a galaxy 10 billion light-years away, and you found it. Take a screenshot. Genuinely, this is the moment the project becomes real.

If you're on the simulated path instead, today is about getting CASA's `simobserve` to produce any cube at all, with a realistic beam size. Same principle: make one picture.

**Day 5 — Work out which line is which.**

You have a bump. Which CO transition is it? This is a small piece of detective work and it's a perfect first real task, because it's self-contained but genuinely matters.

The recipe: find PJ0209's redshift in the observation metadata or the literature. Look up the rest-frame frequency of each CO transition (J=2→1, 3→2, and so on) in **Splatalogue**, a free online database of molecular line frequencies. Then apply the redshift stretch: observed frequency = rest frequency ÷ (1 + z). Compare the answer to where your bump actually sits.

Do this in a small Python script rather than by hand with a calculator, and have it write out a table listing, for each line: its name, rest frequency, predicted observed frequency, and whether you actually see it there. Save it as a file (the plan asks for ECSV format, which is just a text table with a header describing the columns — `astropy` writes it in one line). **Never hard-code a frequency into a script later** — every script should read this table. That habit alone will save you from a whole category of painful, hard-to-find errors.

Where you'll get stuck: your predicted frequency and the observed bump won't quite line up, or two candidate lines will both be plausible. That's usually a redshift that's known only approximately, or a units mix-up (GHz vs MHz — check this first, it's the culprit surprisingly often). Bring the discrepancy to your advisor rather than forcing an answer; "here is exactly where my prediction and the data disagree" is a great thing to walk into a meeting with.

**Day 6/7 — Rest, and then write one page.**

Take real time off; research rewards stamina, not sprinting. Before you close the week, write a one-page summary for yourself: what you installed, what data exists and where it lives, what lines you think you've identified and how confident you are, and the three things that confused you most. Send it to your advisor.

**What "on track" looks like after week one.**

You have a working Python and CASA installation. You've completed one tutorial on someone else's data. You've looked at real PJ0209 data (or made your first simulated cube) and plotted a spectrum. You have a first-draft table of which spectral setup contains which CO line. You have a notes file and a git repository with two or three small scripts in it.

You do **not** have any images of the galaxy, any ratio maps, or any physics yet. That's correct and expected. The matched-imaging work — the technical heart — is roughly weeks 3 through 10, and it's slow because each imaging run can take hours and you'll do many of them. First ratio maps around month four. First temperature-and-density constraints around month five or six.

One last piece of mentor advice: **the single most valuable habit you can build this week is writing down what you did in enough detail to repeat it.** Not for anyone else's benefit — for yours, in October, when you get a strange result and need to know exactly which settings produced it. Every experienced person in this field learned that lesson the expensive way. You can just skip to knowing it.
