(function () {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in-view");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.16, rootMargin: "0px 0px -6% 0px" });

  document.querySelectorAll(".reveal, .timeline-row").forEach((element) => {
    observer.observe(element);
  });

  const panel = document.querySelector("[data-simulator]");
  const slider = document.querySelector("#pauseSlider");
  if (!panel || !slider) {
    return;
  }

  const formatter = new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2
  });

  const cost = Number(panel.dataset.cost || 499);
  const cycleDays = Math.max(Number(panel.dataset.cycleDays || 30), 1);
  const baseEfficiency = Number(panel.dataset.efficiency || 62);
  const dailyRate = cost / cycleDays;

  const pauseDays = document.querySelector("#pauseDays");
  const savingsValue = document.querySelector("#savingsValue");
  const reducedValue = document.querySelector("#reducedValue");
  const efficiencyValue = document.querySelector("#efficiencyValue");
  const ring = document.querySelector("#efficiencyRing");
  const ringLabel = document.querySelector("#ringLabel");

  function updateSimulator() {
    const days = Number(slider.value);
    const savings = dailyRate * days;
    const wasteReduced = Math.min(100, Math.round((days / cycleDays) * 100));
    const efficiency = Math.min(100, Math.round(baseEfficiency + (days / cycleDays) * 100));

    pauseDays.textContent = days;
    savingsValue.textContent = formatter.format(savings);
    reducedValue.textContent = `${wasteReduced}%`;
    efficiencyValue.textContent = `${efficiency}%`;
    ringLabel.textContent = `${efficiency}%`;
    ring.style.setProperty("--value", `${efficiency}%`);
  }

  slider.addEventListener("input", updateSimulator);
  updateSimulator();

  const bootScreen = document.querySelector("#bootScreen");
  if (bootScreen) {
    if (!sessionStorage.getItem("bootSequenceDone")) {
      document.body.classList.add("booting");
      bootScreen.classList.remove("is-hidden");
      
      const bootLines = [
        "> INITIALIZING SUBLIFE ENGINE...",
        "> LOADING SUBSCRIPTION DATA......",
        "> CALCULATING WASTE METRICS.....",
        "> SYSTEM ONLINE ✓"
      ];

      async function typeBootSequence() {
        const lineNodes = bootLines.map((_, index) => document.querySelector(`#bootLine${index}`));
        const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

        if (prefersReduced) {
          lineNodes.forEach((node, index) => {
            node.textContent = bootLines[index];
            node.classList.add("done");
          });
        } else {
          for (let i = 0; i < bootLines.length; i++) {
            const node = lineNodes[i];
            for (let char = 0; char < bootLines[i].length; char++) {
              node.textContent += bootLines[i][char];
              await new Promise((resolve) => setTimeout(resolve, 8));
            }
            node.classList.add("done");
            await new Promise((resolve) => setTimeout(resolve, 70));
          }
        }

        await new Promise((resolve) => setTimeout(resolve, prefersReduced ? 120 : 240));
        bootScreen.classList.add("is-hidden");
        document.body.classList.remove("booting");
        document.body.classList.add("ready");
        sessionStorage.setItem("bootSequenceDone", "true");
        updateSimulator();
      }

      typeBootSequence();
    } else {
      document.body.classList.add("ready");
    }
  } else {
    document.body.classList.add("ready");
  }
})();
