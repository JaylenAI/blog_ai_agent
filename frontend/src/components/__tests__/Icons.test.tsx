import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { Icons } from "../common/Icons";

describe("Icons", () => {
  const iconNames = Object.keys(Icons) as (keyof typeof Icons)[];

  it("exports multiple icon components", () => {
    expect(iconNames.length).toBeGreaterThan(10);
  });

  iconNames.forEach((name) => {
    it(`renders ${name} icon without error`, () => {
      const Icon = Icons[name];
      const { container } = render(<Icon />);
      expect(container.querySelector("svg")).toBeTruthy();
    });
  });

  it("accepts custom size", () => {
    const { container } = render(<Icons.Search s={24} />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("width")).toBe("24");
    expect(svg?.getAttribute("height")).toBe("24");
  });

  it("accepts custom stroke width", () => {
    const { container } = render(<Icons.Plus w={3} />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("stroke-width")).toBe("3");
  });

  it("passes className to svg", () => {
    const { container } = render(<Icons.X className="test-class" />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("class")).toContain("test-class");
  });
});
