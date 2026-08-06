## 1. The Goal

Imagine you want to know how much fuel is left in a car, but you can't open the gas tank. Instead, you have a sensor that detects a chemical that's always mixed into the fuel in a known proportion. Measure the chemical, and you can work out the fuel.

That's roughly the situation with galaxies. Stars form out of cold, dense clouds of gas — mostly hydrogen molecules (H₂). That hydrogen is the fuel supply for making new stars, and how much of it a galaxy has tells you how much star formation it can keep doing. The problem is that cold H₂ is almost invisible: it just sits there without emitting light we can easily detect. So astronomers use a stand-in. Carbon monoxide (CO) gas is mixed in with the hydrogen everywhere in these clouds, it's much easier to detect, and it glows at a very specific radio wavelength. Find the CO, and you've effectively found the hydrogen.

This project uses observations of **20 nearby spiral galaxies** — galaxies with pinwheel arms, like our own Milky Way — taken with ALMA, a huge array of radio dishes in the Chilean desert. Specifically, it uses the ALMA Compact Array (the "ACA"), a set of smaller 7-metre dishes placed close together. Close-together dishes give you blurrier pictures but are much better at seeing big, faint, spread-out things — which is exactly what a galaxy's gas disk is. The observations were made in 2018–2019, they're free and public, and nobody has published a paper using them. That's your opening.

There are two things you'll actually find out, and it's worth being clear that they're different in character.

**The first is about the galaxies.** For each of the 20, you'll measure: how much CO gas it has in total, how fast it's moving away from us (which tells you how far away it is), and — for the ones where the data is good enough — how fast it's spinning. Galaxies rotate, and because of the Doppler effect (the same reason an ambulance siren sounds higher-pitched approaching and lower-pitched receding), the gas coming toward you is shifted slightly bluer and the gas going away is shifted slightly redder. You can literally see the rotation as a color gradient across the galaxy, and turn that into a rotation speed in kilometres per second.

**The second is about the telescope, and it's the more unusual and more valuable half.** You also want to measure how big each galaxy's gas disk is. But here's the catch: these images are blurry — about 5 to 6 arcseconds across, which at these distances is a few thousand light-years. If a galaxy's gas disk is smaller than the blur, you can't measure its size; you can only say "it's smaller than roughly this." The honest scientific question is: *how small is too small?* Most people either guess at this or ignore it. You will **measure** it. You'll take the real data, digitally paste fake galaxies of known size into it, run those fakes through your exact same analysis, and see at what point your analysis stops recovering the right answer. That gives you a hard, defensible floor. Above the floor you quote a real size; below it you quote an upper limit and say so plainly.

That second part is what makes this a good first research project. It teaches the single most important habit in observational science: knowing the difference between what your data actually shows and what you wish it showed.

**What you'll have at the end**, concretely:

- **A catalog** — a table with 20 rows, one per galaxy, listing total CO brightness, distance, rotation speed, gas disk size (or an upper limit), each with an honest error bar. Machine-readable, so anyone can use it.
- **An atlas** — 20 identically formatted pages, one per galaxy, each showing a map of where the gas is, a map of how it's moving, and a plot of its spectrum. All made the same way, so they're genuinely comparable to each other.
- **A calibration result** — a plot showing "here's the smallest gas disk these data can measure, as a function of how bright the galaxy is." This is a reusable result. Anyone else working with ACA data on similar galaxies can cite it.
- **One summary figure** — gas disk size plotted against gas brightness, with arrows for the upper limits, showing whether bigger gas reservoirs live in bigger disks.
- **A code repository** that someone else could download and run to reproduce every number.

You will *not* be answering "why do galaxies form stars." You'll be producing a clean, careful, reusable measurement that other people build on. That's what most real research actually is, and it's a genuinely publishable contribution.

## 2. Skills You'll Need

Be honest with yourself about which of these you have. None of them require years of study, but a few of them require a few focused weeks, and it's much better to know that going in.

**Python — yes, essential, and this is the big one.**
You don't need to be a software engineer. You need to be comfortable with: loops, functions, reading and writing files, and using libraries someone else wrote. Specifically you'll be working with `numpy` (handles grids of numbers — an astronomical image is just a grid of numbers), `matplotlib` (makes plots), and `astropy` (the astronomy toolkit — it reads astronomical image files, converts between coordinate systems, and does distance calculations). You'll also use `spectral-cube`, which is a specialized tool for the 3D data you'll be handling.

*If you don't have this:* work through a general beginner Python course first (any "Python for Scientists" or "Python for Data Analysis" style course — roughly 20–30 hours of real practice, not passive watching). Then do an Astropy tutorial specifically on opening and plotting FITS images. FITS is the standard astronomy image format; think of it as a JPEG that also carries a header full of information about where the telescope was pointing and what the units are. Learning to read a FITS header is a genuine skill and takes about an afternoon.

**The command line and git — needed, but shallow.**
You'll be typing commands in a terminal rather than clicking buttons, and using `git` to track changes to your code. You need maybe ten commands of each. A one-hour introductory tutorial for each is sufficient to start; you'll pick up the rest as you go. Set up git in week one even though it will feel pointless — three months in, when you need to know what your code looked like before you broke it, you will be extremely glad.

**CASA — a specialized program, and you learn it by doing.**
CASA is the software package astronomers use for radio telescope data. It's essentially Python with a large pile of radio-astronomy-specific commands bolted on. You'll use maybe six of them. Nobody learns CASA from a textbook; you learn it from the official ALMA "CASA Guides" tutorials, which walk you through a real dataset step by step. Do one of those guides start-to-finish in week one — not to master it, just to see the shape of the thing.

**Astronomy concepts — moderate depth, all learnable from a good intro textbook chapter or a solid Wikipedia session:**

- *What a spiral galaxy is* — a rotating disk of hundreds of billions of stars plus gas and dust. You should know that they rotate, that they're roughly flat like a dinner plate, and that we see them at random tilts (some face-on like a plate on a table, some edge-on like a plate seen from the side). That tilt matters enormously and comes up constantly in this project.
- *Molecular gas* — the cold, dense gas that stars form out of. Understand roughly why we trace it with CO instead of hydrogen.
- *Flux* — how much energy per second we receive from something. Crucially, flux is not brightness: a dim thing that's close and a bright thing that's far can give the same flux. To get from flux to a real physical quantity (like a mass of gas), you must know the distance.
- *Redshift and the Doppler effect* — everything in the distant universe is moving away from us, which stretches the light to longer wavelengths. The amount of stretch tells you both how fast it's receding and, via the expansion of the universe, how far away it is. These galaxies have redshifts around 1–5%, meaning their light arrives a few percent stretched. This is central: it's how you'll get distances, and it's why each galaxy was observed at a slightly different frequency.
- *Angular size versus physical size* — an arcsecond is a tiny angle (1/3600th of a degree). How many actual light-years an arcsecond corresponds to depends entirely on distance. Converting between the two is something you'll do dozens of times.

**How radio interferometers work — you need the concepts, not the mathematics.**
ALMA isn't one dish; it's many dishes whose signals are combined. Three ideas matter, and you should genuinely understand all three before you interpret anything:

1. The **beam** is the telescope's blur spot — the smallest thing it can distinguish. Every measurement is smeared by the beam. Yours is about 5–6 arcseconds.
2. **The array cannot see structures that are too large.** This is unintuitive and important. An interferometer is blind to smooth, very extended emission — it will simply miss it, and your total flux will come out too low without any warning. This is why the project computes a "largest recoverable scale" for each galaxy.
3. The **primary beam** is the fact that each dish is more sensitive at the center of its field of view than at the edges, so raw images need a correction before the numbers mean anything.

*If you don't have this:* read the introductory chapters of the NRAO "Essential Radio Astronomy" online textbook, and the ALMA Primer. A few days of reading. You can skip every equation on the first pass — come back to them later once you've seen what they do.

**Math — less than you'd fear.**
No calculus is required to start. You need: algebra, logarithms (astronomical quantities span enormous ranges, so plots are usually logarithmic), and basic statistics — what a standard deviation is, what "signal-to-noise ratio" means, what an error bar means. Later you'll do curve fitting, which means "find the parameters that make my model best match my data." You'll use a library that does the hard part; you need to understand what it's doing and when to distrust it. Any introductory statistics-for-scientists resource covers the needed ground.

**Patience with large files and slow computers.**
These datasets are gigabytes. Downloads take hours. Some processing steps take tens of minutes. This isn't a skill exactly, but it shapes how you work: you'll learn to start a long job and go do something else, and to always test new code on the smallest possible piece of data first.

**The one thing that matters more than any of the above:** willingness to write down what you did. Every threshold you pick, every galaxy you exclude, every parameter you tune — write it down the same day, in a notes file in your repository. Research work that isn't recorded may as well not have happened, and you will not remember in March why you made a choice in January.

## 3. Your First Week

A realistic first week. You will not touch all 20 galaxies — you'll be lucky to get one working end-to-end, and that is exactly the right goal. Everything after week one is repetition of what you build here.

**Day 1 — Understand what you're looking at, before you touch a computer.**

Spend the morning reading the project description and writing a one-page explanation *in your own words*, as if to a friend who doesn't do science. If you can't write that page, you don't understand the project yet, and no amount of code will fix that. Bring it to your advisor.

In the afternoon, go look at your galaxies. Take a few of the coordinates from the target list — say J133457.27+340238.7 (which just encodes its position in the sky) — and paste them into an online sky viewer like the Legacy Survey viewer or Aladin. You'll see actual optical pictures. Some will be lovely spirals, some will be small smudges. This is worth doing because it makes them real. These aren't abstract data products; they're twenty specific galaxies, and you're going to spend a semester with them.

Then set up your git repository with the folder structure: `data/` for raw downloads, `products/` for things you make, `code/` for scripts, `figs/` for plots, `catalogs/` for tables. Make an empty README and write one sentence in it. Commit it.

*Where you'll get stuck:* nowhere technically, but you may feel like you haven't done "real work." You have. Understanding the question is the work.

**Day 2 — Install everything. Budget the whole day, seriously.**

Install Miniconda, then create a dedicated environment for this project and install `astropy`, `numpy`, `scipy`, `matplotlib`, `spectral-cube`, `radio-beam`, `astroquery`, and `photutils`. Separately, install CASA — download it from the NRAO site, unpack it, and check that it launches.

Write down the exact versions of everything in your README, including the CASA build string. Use that same CASA version for the entire project, start to finish. Mixing versions midway is a classic way to produce results you can't explain.

Verify the install works: open Python, load astropy, print a version number. Open CASA, type `listobs` and confirm it's recognized. That's enough.

*Where you'll get stuck:* installation. Everyone does. CASA is finicky about operating systems and can be a genuine fight on Windows — if you're on Windows, seriously consider using WSL (Windows Subsystem for Linux) or a Linux machine from the start, because most of the astronomy community's instructions assume Linux or Mac. If you burn the whole day on installs, that is completely normal and not a sign of anything.

**Day 3 — Download one galaxy's data. Just one.**

Go to the ALMA Science Archive, search for project code `2018.1.00473.S`, and look at what comes up. You should see 20 entries. Pick one — a single-pointing one rather than a mosaic, to keep it simple; anything except X1bd2, X1be6, X1bea, X1bf2, or X1c1e.

Download it. This takes a while and arrives as a `.tar` archive that unpacks into a deep nest of directories with cryptic names. Spend real time just exploring that directory tree with `ls`. Find the `.fits` image files. Find the measurement set (the raw calibrated data — a directory, not a file, which is confusing the first time). Find the `.pb` file (the primary beam response) and the `.image` or `.image.pbcor` files.

Write yourself a note explaining what each file type is. You'll refer back to it constantly.

*Where you'll get stuck:* the directory structure is genuinely bewildering, and the download may fail or stall. Try the archive's script-based download option if the browser download is unreliable. Don't download all 20 yet — you'll want to script that later, and you don't need the disk space consumed while you're still learning.

**Day 4 — Open a data cube and actually look at it.**

This is the day it starts feeling like astronomy.

Your main data product is a **spectral line cube**. Think of it as a stack of images: each layer is a picture of the galaxy at one specific frequency, and stacking them gives you a 3D block — two dimensions of sky position, one of frequency. Because of the Doppler effect, frequency is really *velocity*, so a cube is a picture of the galaxy at each different speed of gas. That's how you see rotation: the gas on one side of the galaxy shows up in the low-velocity layers and the other side in the high-velocity layers.

Open your cube in Python with `spectral-cube` and print the header. Find and write down: the beam size (BMAJ, BMIN, BPA — the blur spot's major axis, minor axis, and rotation angle), the pixel scale, the number of channels, the frequency of the first and last channel, and the width of each channel in km/s. Note whether the image has already had the primary beam correction applied.

Then make a picture. Plot one single channel. Then plot a channel from the very edge of the frequency range, where there shouldn't be any galaxy emission — that one should look like pure noise. Compare the two. If you can see something in the middle channel that isn't in the edge channel, you have just detected molecular gas in another galaxy with your own hands. Take a moment with that.

Also install and open the data in CARTA, a browser-based viewer for radio cubes. Being able to scroll through channels interactively and watch the emission move across the galaxy is worth an enormous amount for building intuition, and it's how you'll catch problems later.

*Where you'll get stuck:* axis conventions. Astronomical images are often stored with axes in an order you don't expect, and right ascension increases leftward rather than rightward. Expect at least one confusing hour where your image is flipped or transposed. Everyone goes through it.

**Day 5 — Make your first moment map and your first spectrum.**

A **moment-0 map** collapses the cube along the frequency axis: for each pixel, add up all the channels. The result is a single 2D image showing total gas at each position — essentially "here's where the gas is." A **moment-1 map** instead computes, for each pixel, the average velocity of the gas there. That one is "here's how the gas is moving," and in a rotating galaxy it looks like a smooth gradient from one side to the other.

Make both, crudely, for your one galaxy. Don't worry about doing it correctly yet — no careful masking, no primary beam correction, just sum the channels that obviously contain signal and plot the result. The point is to see it.

Then make an **integrated spectrum**: add up all the pixels in a box around the galaxy for each channel, and plot the total against velocity. If the galaxy is well detected you should see a bump, and if it's a well-behaved rotating spiral seen at an angle, the bump may have two horns — higher on both edges than the middle. Those horns come from the flat outer parts of the rotation curve, where lots of gas shares the same velocity. Seeing that shape for the first time is one of the more satisfying moments in radio astronomy.

*Where you'll get stuck:* the flux units. Radio maps come in "Jy/beam" — janskys per beam — and to get a total flux in janskys you must divide by the number of pixels in a beam. Get this wrong and every number downstream is off by a large factor. This is probably the single most common beginner error in radio astronomy. Work it out carefully on paper, write the arithmetic in your notes, and check that your answer is a sensible number.

**Day 6 — Verify the line, and measure a real redshift.**

Now do a piece of genuine science with a real, defensible result.

The project description says the CO line you're after sits at a rest frequency of 230.538 GHz — its frequency in a laboratory, at rest. But that description was auto-generated and explicitly flags that it needs checking. So check it: go to Splatalogue, the online database of molecular line frequencies, look up carbon monoxide J=2–1, and record the number and its source in your README. This takes fifteen minutes and it is exactly the kind of thing that separates careful work from careless work. While you're there, confirm that the other bright molecular lines nearby (¹³CO, C¹⁸O, CN) don't fall inside your observed frequency window and can't be confusing you.

Then measure your galaxy's redshift yourself. Take the spectrum from Day 5, find the frequency at the center of the line, and compare it to the verified rest frequency. The fractional shift is the redshift. Plug that into astropy's cosmology module to get a distance, and from the distance get the conversion between arcseconds and kiloparsecs for that galaxy.

Note what you just did: the project description gave you approximate redshifts, but those were *reverse-engineered* from which frequency the telescope was tuned to — essentially "the observers must have thought it was here." Yours comes from the actual detected line. That's a measurement, not an assumption, and it's better. Keep both in your catalog and label which is which.

*Where you'll get stuck:* velocity conventions. There are multiple, mutually incompatible ways to convert frequency to velocity (radio versus optical definition) and multiple reference frames (relative to the Sun, relative to the local standard of rest). Getting these mixed up produces errors of tens of km/s that are large enough to matter but small enough that you might not notice. Find out which convention your file header uses and write it down explicitly. Ask your advisor if it's not obvious — this is a completely reasonable question and everyone has been confused by it.

**Day 7 — Turn what you did into a script, and write it up.**

Everything so far was probably done in a notebook with a lot of trial and error. Now turn the working parts into an actual script that takes a target name, reads its file paths from a configuration file, and produces the moment maps and spectrum. It doesn't need to be elegant. It needs to run twice and give the same answer both times.

Make a `targets.yaml` configuration file with one entry per galaxy, holding its UID, coordinates, and file paths. Every per-galaxy setting lives there and *never* hard-coded in a script. This sounds like fussy bookkeeping. It is the thing that will let you run all 20 galaxies with one command in a month, and it's what makes the fake-source injection test in the second half of the project meaningful at all — the fakes have to go through byte-for-byte identical code as the real galaxies.

Then write a page of notes: what you did, what confused you, what you're unsure about, what you want to ask. Commit everything to git.

**What "done" looks like at the end of week one**

You should have:
- A working software environment with versions recorded
- One galaxy's data downloaded and understood
- A first-look moment-0 map, moment-1 map, and spectrum for it
- A verified rest frequency and a redshift you measured yourself
- A rough script and a config file
- A running notes file full of questions

You should **not** have all 20 galaxies, careful masking, any size fitting, or any final numbers. If someone told you week one should produce more than this, they've forgotten what week one is like.

**The most common way this week goes wrong** is spending five days fighting installations and downloads and reaching Friday with no picture of a galaxy. If Wednesday arrives and you're still stuck on setup, stop and ask for help immediately — an advisor or a grad student can often fix in ten minutes something you'd fight for two days. Asking early is not weakness; it's the correct move, and experienced researchers do it constantly.

**One habit to start on Day 1 and never drop:** keep a dated log of what you tried and what happened, including failures. Three months from now you will find a number in your catalog and have no idea where it came from. The log is what saves you. It is also, when the time comes, most of your thesis methods chapter already written.
