# DraftChat Component

This directory contains components for the DraftChat page, which is displayed after a user completes the initial chat flow (when `initialChatStep === "done"`).

## Component Structure

- **DraftChat.jsx**: Main container component that renders the progress indicator, chat section, and draft section.
- **ProgressIndicator.jsx**: Displays the project title and progress steps at the top of the page.
- **ChatSection.jsx**: Left side of the page, provides a chat interface for discussing the draft.
- **DraftSection.jsx**: Right side of the page, displays the draft content with a navigation sidebar.

## Usage

The DraftChat component is conditionally rendered in `App.jsx` when the `initialChatStep` context value is set to `"done"`. This happens after the user has submitted an idea, approved it, and selected a title.

```jsx
// Example usage in App.jsx
import DraftChat from "./components/DraftChat";
import { useChat } from "./ChatContext";

function AppContent() {
  const { initialChatStep } = useChat();

  return <>{initialChatStep !== "done" ? <InitialChat /> : <DraftChat />}</>;
}
```

## Styling

The components use Tailwind CSS for styling, maintaining a consistent design language with the rest of the application.
