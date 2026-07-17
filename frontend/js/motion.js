// js/motion.js
import { animate, inView } from "https://cdn.jsdelivr.net/npm/motion@latest/+esm";

export function animateCards(selector = ".prod-card, .cat-card") {
  inView(selector, (element) => {
    animate(element, { opacity: [0, 1], y: [20, 0] }, { duration: 0.5 });
  });
}