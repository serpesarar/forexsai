import { render, screen } from "@testing-library/react";
import OrderBlockPanel from "../components/OrderBlockPanel";

describe("OrderBlockPanel", () => {
  it("renders heading", () => {
    render(<OrderBlockPanel />);
    expect(screen.getByText(/Order Block Detector/i)).toBeInTheDocument();
  });
});
