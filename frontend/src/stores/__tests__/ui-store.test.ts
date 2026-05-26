import { describe, it, expect, beforeEach } from "vitest";
import { useUIStore } from "../ui-store";
import { act } from "@testing-library/react";

beforeEach(() => {
  act(() => {
    useUIStore.setState({
      sidebarOpen: true,
      rightPanelOpen: true,
      rightPanelTab: "pipeline",
      theme: "dark",
      density: "default",
      accentHue: 255,
      sidebarPanel: null,
      publishKitOpen: false,
      editorMode: "view",
      editDraft: null,
      userProfile: {
        displayName: "Jaylen H.",
        blogUrl: "jaylenhan.tistory.com",
        workspaceName: "AI의 정석",
        avatarInitials: "JH",
      },
    });
  });
});

describe("useUIStore", () => {
  it("initializes with default values", () => {
    const state = useUIStore.getState();
    expect(state.sidebarOpen).toBe(true);
    expect(state.rightPanelOpen).toBe(true);
    expect(state.rightPanelTab).toBe("pipeline");
    expect(state.density).toBe("default");
    expect(state.accentHue).toBe(255);
    expect(state.sidebarPanel).toBeNull();
    expect(state.publishKitOpen).toBe(false);
    expect(state.editorMode).toBe("view");
    expect(state.editDraft).toBeNull();
  });

  it("toggleSidebar flips sidebarOpen", () => {
    act(() => useUIStore.getState().toggleSidebar());
    expect(useUIStore.getState().sidebarOpen).toBe(false);
    act(() => useUIStore.getState().toggleSidebar());
    expect(useUIStore.getState().sidebarOpen).toBe(true);
  });

  it("toggleRightPanel flips rightPanelOpen", () => {
    act(() => useUIStore.getState().toggleRightPanel());
    expect(useUIStore.getState().rightPanelOpen).toBe(false);
  });

  it("setRightPanelTab updates tab", () => {
    act(() => useUIStore.getState().setRightPanelTab("references"));
    expect(useUIStore.getState().rightPanelTab).toBe("references");
  });

  it("setTheme updates theme", () => {
    act(() => useUIStore.getState().setTheme("light"));
    expect(useUIStore.getState().theme).toBe("light");
  });

  it("setDensity updates density", () => {
    act(() => useUIStore.getState().setDensity("compact"));
    expect(useUIStore.getState().density).toBe("compact");
    act(() => useUIStore.getState().setDensity("spacious"));
    expect(useUIStore.getState().density).toBe("spacious");
  });

  it("setAccentHue updates hue", () => {
    act(() => useUIStore.getState().setAccentHue(120));
    expect(useUIStore.getState().accentHue).toBe(120);
  });

  it("setSidebarPanel toggles panel (same value → null)", () => {
    act(() => useUIStore.getState().setSidebarPanel("pipelines"));
    expect(useUIStore.getState().sidebarPanel).toBe("pipelines");
    act(() => useUIStore.getState().setSidebarPanel("pipelines"));
    expect(useUIStore.getState().sidebarPanel).toBeNull();
  });

  it("setSidebarPanel switches between panels", () => {
    act(() => useUIStore.getState().setSidebarPanel("pipelines"));
    act(() => useUIStore.getState().setSidebarPanel("settings"));
    expect(useUIStore.getState().sidebarPanel).toBe("settings");
  });

  it("setPublishKitOpen updates state", () => {
    act(() => useUIStore.getState().setPublishKitOpen(true));
    expect(useUIStore.getState().publishKitOpen).toBe(true);
    act(() => useUIStore.getState().setPublishKitOpen(false));
    expect(useUIStore.getState().publishKitOpen).toBe(false);
  });

  it("setEditorMode to edit keeps editDraft undefined", () => {
    act(() => useUIStore.getState().setEditorMode("edit"));
    expect(useUIStore.getState().editorMode).toBe("edit");
    expect(useUIStore.getState().editDraft).toBeUndefined();
  });

  it("setEditorMode to view clears editDraft", () => {
    act(() => {
      useUIStore.getState().setEditorMode("edit");
      useUIStore.getState().setEditDraft("draft content");
    });
    expect(useUIStore.getState().editDraft).toBe("draft content");

    act(() => useUIStore.getState().setEditorMode("view"));
    expect(useUIStore.getState().editDraft).toBeNull();
  });

  it("setEditDraft updates draft", () => {
    act(() => useUIStore.getState().setEditDraft("새 초안"));
    expect(useUIStore.getState().editDraft).toBe("새 초안");
    act(() => useUIStore.getState().setEditDraft(null));
    expect(useUIStore.getState().editDraft).toBeNull();
  });

  it("initial userProfile has correct defaults", () => {
    const { userProfile } = useUIStore.getState();
    expect(userProfile.displayName).toBe("Jaylen H.");
    expect(userProfile.blogUrl).toBe("jaylenhan.tistory.com");
    expect(userProfile.workspaceName).toBe("AI의 정석");
    expect(userProfile.avatarInitials).toBe("JH");
  });

  it("setUserProfile partial update preserves other fields", () => {
    act(() => useUIStore.getState().setUserProfile({ displayName: "New Name" }));
    const { userProfile } = useUIStore.getState();
    expect(userProfile.displayName).toBe("New Name");
    expect(userProfile.blogUrl).toBe("jaylenhan.tistory.com");
    expect(userProfile.workspaceName).toBe("AI의 정석");
    expect(userProfile.avatarInitials).toBe("JH");
  });

  it("setUserProfile updates multiple fields at once", () => {
    act(() =>
      useUIStore.getState().setUserProfile({
        displayName: "Alice K.",
        blogUrl: "alice.blog.com",
        avatarInitials: "AK",
      }),
    );
    const { userProfile } = useUIStore.getState();
    expect(userProfile.displayName).toBe("Alice K.");
    expect(userProfile.blogUrl).toBe("alice.blog.com");
    expect(userProfile.avatarInitials).toBe("AK");
    expect(userProfile.workspaceName).toBe("AI의 정석");
  });
});
