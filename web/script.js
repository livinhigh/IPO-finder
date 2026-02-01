const apiBase = "http://localhost:8000";
const emailInput = document.getElementById("email");
const subscribeButton = document.getElementById("subscribe");
const toast = document.getElementById("toast");
const runTime = document.getElementById("run-time");

const showToast = (message) => {
  toast.textContent = message;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 2500);
};

const to12Hour = (time24) => {
  const match = /^([01]?\d|2[0-3]):([0-5]\d)$/.exec(time24 || "");
  if (!match) return null;

  const hours = Number(match[1]);
  const minutes = match[2];
  const period = hours >= 12 ? "pm" : "am";
  const hour12 = hours % 12 || 12;
  return `${hour12}:${minutes} ${period}`.replace(":00", "");
};

const loadConfig = async () => {
  try {
    const response = await fetch("/static/config.json", { cache: "no-store" });
    if (!response.ok) {
      return;
    }
    const data = await response.json();
    if (data.triggerTime) {
      const formatted = to12Hour(data.triggerTime);
      if (formatted) {
        runTime.textContent = formatted;
      }
    }
  } catch {
    // Ignore config errors
  }
};

const subscribe = async () => {
  const email = emailInput.value.trim();
  if (!email) {
    showToast("Please enter a valid email");
    return;
  }

  subscribeButton.disabled = true;

  try {
    const response = await fetch(`${apiBase}/subscribe`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });

    const data = await response.json();

    if (response.ok) {
      showToast(data.message || "Subscribed");
      emailInput.value = "";
    } else {
      showToast(data.detail || "Error subscribing");
    }
  } catch {
    showToast("Error subscribing");
  } finally {
    subscribeButton.disabled = false;
  }
};

subscribeButton.addEventListener("click", subscribe);

loadConfig();
