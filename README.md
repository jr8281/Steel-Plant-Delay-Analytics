# Steel Plant Delay Analytics System
## Admin & Operator Dashboard Redesign Specification

---

# Objective

Redesign the existing Admin and Operator dashboards into a professional enterprise analytics platform.

The visual language MUST remain consistent with the Login Page.

The dashboard should resemble software used inside industrial organizations such as Siemens, Honeywell, ABB, GE Digital or Tata Steel.

Do NOT create a generic Streamlit dashboard.

The application must feel like an enterprise operational intelligence platform.

---

# Theme

Continue using the exact design language from the Login Page.

Theme:
- Dark Industrial Theme

Primary Background:
#0F172A

Sidebar:
#111827

Cards:
#1E293B

Accent Blue:
#2563EB

Accent Green:
#22C55E

Warning:
#F59E0B

Danger:
#EF4444

Text:
#F8FAFC

Secondary Text:
#94A3B8

Use glassmorphism only where appropriate.

Keep shadows soft.

Rounded corners:
16px–20px

Consistent spacing throughout.

---

# Typography

Font:
Inter

Hierarchy:

Application Title
32px

Section Heading
26px

Card Title
16px

Body
14px

Sidebar
15px

Buttons
15px SemiBold

---

# Dashboard Layout

The dashboard consists of three sections.

1. Header
2. Sidebar
3. Main Content

---------------------------------------------------

HEADER

Height:
90px

Contains:

Left

RINL Logo

Application Name

Steel Plant Delay Analytics

Subtitle

Enterprise Operational Intelligence

Right

Current Logged User

Role

Logout Button

(Current Date & Time)

Do NOT place navigation in the header.

Navigation stays inside sidebar.

---------------------------------------------------

SIDEBAR

Width:
280px

Same dark background as login page.

Logo should match login page.

Navigation:

Home

Dashboard

upload CSV
(Admin only)

Dataset Overview

AI Assistant

Dark Mode / Light Mode Toggle

Logout

Operator Dashboard should NOT contain Export CSV.

Dark Mode toggle should appear below AI Assistant.

Footer:

© 2026 Steel Plant Delay Analytics

---------------------------------------------------

MAIN CONTENT

Main content changes based on navigation.

Do NOT reload the entire application.

Only update content panel.

Maintain smooth transitions.

---

# Home Page

(Will be described later.)

Create placeholder section.

Keep layout ready.

---

# Dashboard

(Will be described later.)

Create empty dashboard container.

Do NOT populate charts.

Keep layout placeholders only.

---

# Upload CSV

Admin only.

Placeholder page.

Content will be implemented later.

---

# Dataset Overview

Placeholder.

Header

Description

Empty content area.

---

# AI Assistant

Placeholder.

Large chat container.

Input at bottom.

Assistant icon.

Empty state message.

---

# Dark Mode

Implement proper theme switching.

Requirements:

Toggle button.

Remember selection using Streamlit Session State.

Switch colors dynamically.

No page refresh.

Dark mode is default.

---

# Navigation

Navigation should use Session State.

Do NOT reload entire application.

Active navigation should have:

Blue background

Rounded corners

White icon

White text

Hover effects.

---

# Cards

Reusable design.

Rounded:
18px

Padding:
24px

Shadow:
Soft

Border:
1px rgba(255,255,255,.06)

Hover:

Lift slightly.

---

# Buttons

Primary

Blue gradient

Rounded

Large

Hover

Glow

Secondary

Transparent

Border

---

# Animations

Subtle only.

Fade In

Card Lift

Button Hover

Page Transition

No excessive motion.

---

# Responsiveness

Desktop First.

Support:

1920px

1600px

1440px

1366px

1280px

Tablets if possible.

Do not break layout.

---

# Folder Structure

frontend/

assets/

images/

styles/

theme.css

dashboard.css

sidebar.css

components.css

pages_content/

home.py

graphs.py

dataset_overview.py

assistant.py

export_csv.py

utils.py

---

# CSS Rules

Separate CSS.

Do NOT place long inline CSS inside Python files.

Create reusable classes.

Avoid duplicated styling.

---

# Streamlit Requirements

Keep current authentication.

Keep existing FastAPI integration.

Keep JWT authentication.

Keep session state.

Do NOT modify backend.

Only redesign frontend.

---

# Constraints

Do NOT change:

Authentication

Database

Backend

API Calls

Business Logic

Only redesign UI.

---

# Deliverables

1. Modern enterprise dashboard.

2. Reusable CSS architecture.

3. Shared design language with login page.

4. Responsive sidebar.

5. Professional navigation.

6. Theme switcher.

7. Clean folder organization.

8. Modular components.

9. No inline CSS unless absolutely necessary.

10. Production-quality frontend.