# Prompt Document: CAI Frontend Generation & Backend Integration

**Objective**: Use this document to generate a high-end, production-ready React web application that perfectly integrates with an existing FastAPI backend. The UI is designed to be highly bespoke, relying on a 3D kinetic background, click-based vault dial navigation, and native iOS-style glassmorphism.

## 1. Core Tech Stack
* **Framework**: React 18+ (Vite)
* **Styling**: Tailwind CSS
* **Icons**: `lucide-react`
* **Charts**: `recharts`
* **3D Canvas**: `three` (for ASCIIText background)
* **API Client**: `axios`

---

## 2. Global Brand & Aesthetic Directives
* **Nomenclature**: The app is strictly named "CAI".
* **Color Palette**: 
  * Background: Midnight Blue (`#0f172a` to `#020617`)
  * Accents: Warm Beige (`#c4a882`)
  * Status: Success (`#10b981`), Warning (`#f59e0b`), Error (`#ef4444`)
  * Typography: Stark monochrome (White, Slate Gray).
* **Glassmorphism**: All containers use native CSS glass (`bg-white/5`, `backdrop-blur-xl`, `border border-white/10`).

---

## 3. Application State & Routing (`App.tsx`)
* **State Management**: Lift session state to the root `App.tsx` to persist data between page changes without Redux.
  * `currentPage`: ('dashboard', 'upload', 'review', 'deductions', 'settings')
  * `selectedDocId`: Tracks the active document for review.
  * `sessionUploads`: Array holding recent uploads to persist them on the Upload page until a hard browser refresh.
* **Routing Logic**: Pass a `navigateTo(page, docId?)` function down to all pages.

---

## 4. API Client Integration (`client.ts`)
Map `axios` to the following exact backend routes with a `/api/v1` base URL:
* `uploadDocument(file: File)`: `POST /documents/upload` (multipart/form-data)
* `getAnalysisStatus(docId: string)`: `GET /documents/analysis/{docId}`
* `getLatestDocument()`: `GET /documents/latest`
* `getTaxSummary()`: `GET /reports/summary`

---

## 5. Z-Index Layout Architecture
1. **Layer 1 (Background)**: `ASCIIText.tsx` (`z-0`, `pointer-events: none`). Absolute positioned, continuously animating 3D mesh. Fixed top-left (`x:-250, y:300`).
2. **Layer 2 (Navigation)**: `OptionWheel.tsx` (`z-50`). Fixed to the left edge (`w-64`), containing a vertical list of menu items.
3. **Layer 3 (Main Content)**: `Layout.tsx` (`z-20`). Left padding (`pl-64`) to accommodate the menu, housing a centered `max-w-6xl` container for pages.

---

## 6. Core Component Specifications

### 6.1 `OptionWheel.tsx` (Navigation)
* **Behavior**: A sleek, click-friendly vertical navigation bar (not a physics drag wheel).
* **Design**: Uses a frosted glass pill-shaped container. Active items illuminate in `var(--color-beige)` and gain a subtle background highlight; inactive items remain `slate-400`. Includes Lucide icons.

### 6.2 `Upload.tsx` & `DocumentCard.tsx`
* **State**: Receives `sessionUploads` from `App.tsx` via props so uploaded items aren't lost on unmount.
* **Flow**: When a file drops, call `uploadDocument`. The API immediately returns the completed extraction. Map the result instantly to `sessionUploads`.
* **Card Design**: `DocumentCard` is a 2-row bounded flex container with `truncate` applied to the filename to prevent overflow, accompanied by status badges (Pending, Complete, Error) and a confidence score pill. Clicking it triggers `onNavigate('review', id)`.

### 6.3 `ReviewPanel.tsx` (Auto-Loading & Display)
* **Logic**: 
  * If `docId` is provided, call `getAnalysisStatus(docId)`.
  * If `docId` is null, automatically call `getLatestDocument()` to auto-load the most recently processed bill.
* **Loading State**: Must show a spinner while fetching data to prevent premature short-circuiting.
* **Extracted Fields Display**: Maps JSON response cleanly to: Vendor Name, Date, Total Amount (Formatted in INR `₹`), Tax Category, Confidence Score.

### 6.4 `Dashboard.tsx`
* **Logic**: Fetches `getTaxSummary()` on mount.
* **Layout**: Displays `MetricCard` components across the top for Total Deductions, Estimated Tax, etc. Uses `recharts` for a visual pie breakdown of expenses by category.

---

## 7. Execution Prompt for AI
> "Read this PRD and generate the React application. Start by setting up the Vite environment, Tailwind config, and API client. Then, build the components starting from `Layout` and `OptionWheel` up through the `Upload` and `Review` screens. Ensure strict adherence to the glassmorphism aesthetic and API paths."
