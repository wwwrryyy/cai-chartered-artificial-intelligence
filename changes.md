Product Requirements Document: CAI Frontend Overhaul
1. Executive Summary
Project Name: CAI
Objective: Replace the existing, generic AI-generated frontend with a highly bespoke, interactive, and minimal single-page application. The interface will prioritize deep technical aesthetics, relying on a 3D kinetic background, tactile mechanical scrolling, and native iOS-style glassmorphism to separate heavy financial data from the visual layer.
Core Tech Stack: React, Tailwind CSS, Three.js.
2. Global Brand & Aesthetic Directives
⚬ Nomenclature: Complete global replacement of the term "Tax AI" with "CAI" across the entire application interface and document metadata.
⚬ Color Palette: A premium dark-mode foundation. Deep midnight blue transitioning into warm beige, utilizing stark monochrome (blacks, whites, slate grays) for functional UI elements.
⚬ Typography: A strict geometric sans-serif for all UI readouts and data tables, contrasting with a monospace font strictly reserved for the 3D background canvas and specific numeric data points.
⚬ Whitespace: Implement aggressive negative space. Containers must not feel cramped; data should be allowed to breathe within expansive, borderless or finely bordered glass panels.
3. Core Layout Architecture
The application layout relies on a strict, three-layer Z-index hierarchy to create depth and focus without clutter.
⚬ Layer 1 (Background Canvas): An absolute-positioned, full-bleed 3D typographic wave running continuously behind all other elements.
⚬ Layer 2 (Navigation Overlay): A tactile, left-anchored curved wheel overlaying the canvas, acting as the sole routing mechanism.
⚬ Layer 3 (Data Containers): The primary right-aligned viewing pane where backend tax data, file upload zones, and calculation metrics are rendered inside frosted glass containers.
4. Component Specifications
4.1 Background Canvas (ASCIIText)
The application background will utilize the Three.js-powered ASCIIText visual component to render a continuous, undulating 3D plane.
⚬ Rendered Text: The string "CAI" must be drawn onto the plane.
⚬ Visual Configuration: Waves must be enabled. The ASCII glyph size should be set to 10 for a dense, highly technical grid.
⚬ Palette Override: The default pink/orange gradient in the component's styling must be overridden with a radial gradient transitioning from midnight blue to a warm, premium beige.
⚬ Behavior: The canvas must be entirely un-clickable (pointer events disabled) so it does not interfere with the active glass panels sitting above it.
4.2 Interactive Navigation (OptionWheel)
Standard sidebars are to be entirely removed and replaced with a mechanical, tactile scroll wheel component anchored to the left side of the screen.
⚬ Routing Items: Dashboard, Upload, Review, Deductions, Settings.
⚬ Aesthetic Configuration: The resting text color should be a muted slate gray, illuminating to warm beige as an item reaches the active center position. The font size should be dialed down to ensure a sharp, understated look.
⚬ Physics & Feel: The curve should be slightly flattened, and the drag smoothing increased to simulate the heavy, precise feel of a physical vault dial.
⚬ Audio Feedback: A high-quality, soft mechanical click audio file must be triggered upon item selection to provide tactile feedback.
4.3 Content Panels (Native iOS Liquid Glass)
All heavy data, forms, and charts must be isolated from the kinetic background using native CSS glassmorphism, completely avoiding third-party wrapper dependencies.
⚬ Visual Logic: The glass effect must utilize a heavy backdrop blur combined with a significant backdrop saturation boost (e.g., 180 percent) to ensure the ASCII background bleeds through vibrantly without compromising text legibility.
⚬ Container Styling: The background of the panel itself should be an ultra-sheer white (roughly 5 percent opacity).
⚬ Edge Definition: The defining premium characteristic must be a razor-thin, 1-pixel solid border utilizing a highly transparent white, giving the glass a physical, precision-cut edge.
⚬ Application: This exact utility styling must be applied to the main routing viewport, the drag-and-drop file upload zone, and individual metric badges across the dashboard.
5. Execution Protocol for Claude Opus
1. Initialize the React environment and install the Three.js dependency required for the background canvas.
2. Incorporate the ASCIIText and OptionWheel component source files into the project structure.
3. Delete all existing AI-generated layout components (Header, Sidebar, default Dashboard wrapper).
4. Construct the layout file strictly adhering to the three-layer architecture defined in Section 3.
5. Generate a global CSS utility class for the iOS liquid glass effect as defined in Section 4.3 and apply it to the main content pane.
6. Wire the OptionWheel component's change event to the React Router implementation to handle seamless switching between the core application views.