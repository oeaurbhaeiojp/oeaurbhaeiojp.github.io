# Rouzbeh Pourjafarian — Personal Academic Website

A single self-contained `index.html` (pure HTML/CSS/JS, no frameworks, no build
step) for hosting on **GitHub Pages**. All course, certificate, and teaching
content is **data-driven**: you edit small JavaScript objects near the top of the
`<script>` block in `index.html` and upload PDFs/images to the matching folders.
You never touch the layout code.

---

## 1. Set up GitHub Pages

1. Make sure this repository is named **`<your-username>.github.io`** (it already
   is) and pushed to GitHub.
2. On GitHub, go to **Settings → Pages**.
3. Under **Build and deployment → Source**, choose **Deploy from a branch**.
4. Select the branch you publish from (e.g. `main`) and folder **`/ (root)`**, then
   **Save**.
5. Wait ~1 minute. Your site is live at **`https://<your-username>.github.io/`**.

Every time you push to that branch, the site redeploys automatically.

---

## 2. Add your profile photo

Drop a square image at:

```
assets/photo.jpg
```

(~400×400 px works well.) Until you add it, the hero shows a small "Add photo"
placeholder. No code change needed — the filename is fixed.

---

## 3. Add a new homework to a course

1. **Edit the data.** In `index.html`, find `COURSES_DATA` and locate the course.
   Add an entry to its `homeworks` array:

   ```js
   homeworks: [
     { id: 1, topic: "Thin-walled beam analysis" },
     { id: 2, topic: "Shear flow in closed sections" },
     { id: 3, topic: "Your new homework topic" }   // <-- new
   ]
   ```

2. **Upload the PDF.** Put the file at:

   ```
   assets/courses/<course-slug>/hw/hw<id>.pdf
   ```

   The number in the filename must match the `id`. For example `id: 3` →
   `hw3.pdf`.

That's it — a new **HW 3** card appears, and clicking it slides open the PDF
viewer.

---

## 4. Add a new project to a course

1. **Edit the data.** In the course's `projects` array, add an object with **all**
   fields:

   ```js
   {
     slug: "my-new-project",            // kebab-case; also the folder name
     title: "My New Project",
     description: "One-line summary of the project.",
     tags: ["ABAQUS", "FEM"],           // coral badges
     hasReport: true,                   // shows report.pdf viewer
     hasSlides: true,                   // shows slides.pdf viewer
     hasCode: true,                     // shows a GitHub button
     code: "https://github.com/you/repo" // used only when hasCode is true
   }
   ```

2. **Upload the files** into a folder named after the `slug`:

   ```
   assets/courses/<course-slug>/projects/<project-slug>/report.pdf
   assets/courses/<course-slug>/projects/<project-slug>/slides.pdf
   ```

   Only upload what you enabled: `report.pdf` if `hasReport`, `slides.pdf` if
   `hasSlides`. Set a flag to `false` (or omit) to hide that block.

Clicking the project card expands it inline to show the report, slides, and/or
code button.

---

## 5. Add a new course

1. **Edit the data.** Add a new top-level key to `COURSES_DATA`. The **key is the
   course slug** (kebab-case) and also the asset folder name:

   ```js
   "finite-element-methods": {
     name: "Finite Element Methods",
     homeworks: [
       { id: 1, topic: "Shape functions" }
     ],
     projects: [
       {
         slug: "plate-bending-fem",
         title: "Plate Bending FEM",
         description: "...",
         tags: ["Python"],
         hasReport: true,
         hasSlides: false,
         hasCode: false,
         code: ""
       }
     ]
   }
   ```

   The left course sidebar and its content are generated automatically — no
   layout edits.

2. **Create the folders** and upload files:

   ```
   assets/courses/finite-element-methods/hw/
   assets/courses/finite-element-methods/projects/plate-bending-fem/
   ```

---

## 6. Add a new certificate

1. **Edit the data.** Add an object to `CERTIFICATES_DATA`:

   ```js
   {
     slug: "deep-learning",          // -> assets/certificates/deep-learning.jpg
     name: "Deep Learning",
     issuer: "Some Institute",
     date: "06/26",
     summary: "Optional one-line summary."   // omit to hide
   }
   ```

2. **Upload the thumbnail** at `assets/certificates/<slug>.jpg`. Until then a
   placeholder label is shown.

---

## 7. Update your bio or research entries

- **Bio:** edit the paragraph inside the `<section id="about">` block in
  `index.html`.
- **Research experience:** edit the `<article class="tl-card">` blocks inside
  `<section id="research">`. Newest first. Each card has a `date`, an `h3` title,
  a `sub` line (role · org · advisor), and a description paragraph.
- **Teaching:** edit the `TEACHING_DATA` array (grouped by semester).
- **Hero pills / skills:** edit the `pill` spans in the hero and the
  `<section id="skills">` block.

---

## 8. Folder naming conventions

Use **kebab-case** (lowercase, words joined by hyphens) for every slug and
folder. The slug in the data **must exactly match** the folder name.

| Thing        | Data field            | Folder / file                                              |
|--------------|-----------------------|------------------------------------------------------------|
| Course       | key in `COURSES_DATA` | `assets/courses/<course-slug>/`                            |
| Homework     | `id`                  | `assets/courses/<course-slug>/hw/hw<id>.pdf`              |
| Project      | `slug`                | `assets/courses/<course-slug>/projects/<project-slug>/`  |
| Report       | `hasReport`           | `.../projects/<project-slug>/report.pdf`                  |
| Slides       | `hasSlides`           | `.../projects/<project-slug>/slides.pdf`                  |
| Certificate  | `slug`                | `assets/certificates/<slug>.jpg`                          |

Examples: `theory-of-plates-and-shells`, `wing-structural-analysis`.

---

## 9. Redact a PDF before uploading

To remove sensitive content before publishing publicly:

1. Go to **[PDF24.org](https://tools.pdf24.org/)** — free, browser-based, no
   install, processed in your browser.
2. Use the **"Redact PDF"** tool (or "Edit PDF") to black out text/figures, or
   delete pages you don't want public.
3. Export and save the redacted file, then upload **that** version.

Every PDF viewer on the site already shows the notice *"Some content is redacted
for privacy. Need the full version?"* with Email and LinkedIn buttons, so viewers
know to reach out for unredacted copies.

> Tip: flattening/redacting (not just drawing a black box in a normal editor)
> ensures the hidden text is actually removed, not just visually covered.

---

## 10. Test the site locally before pushing

Because the site loads PDFs via relative paths, open it through a local web
server (not by double-clicking the file):

```bash
# from the repository root
python -m http.server 8000
```

Then open **http://localhost:8000** in your browser. Edit, refresh, and once
it looks right:

```bash
git add .
git commit -m "Update course content"
git push
```

GitHub Pages redeploys automatically.

---

## Project structure

```
index.html                 # the entire site (HTML + CSS + JS)
README.md                  # this guide
assets/
  photo.jpg                # your profile photo (add this)
  certificates/
    <slug>.jpg             # certificate thumbnails
  courses/
    <course-slug>/
      hw/
        hw1.pdf, hw2.pdf   # homework PDFs
      projects/
        <project-slug>/
          report.pdf
          slides.pdf
```

`NOTE.txt` files in the asset folders are just reminders of what goes where — you
can delete them once you've added real content.
