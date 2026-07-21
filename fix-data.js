// SafarMa data-schema hotfix.
// Older compact destination rows contained one additional numeric cost column.
// The original mapper therefore shifted good-months, safety and transport by one position.
D.forEach((destination) => {
  if (!Array.isArray(destination.good)) {
    const goodMonths = Array.isArray(destination.safe) ? destination.safe : [];
    const safetyLevel = Number.isFinite(destination.move) ? destination.move : 2;
    destination.extraDailyCost = Number(destination.good) || 0;
    destination.good = goodMonths;
    destination.safe = safetyLevel;

    const carDestinations = new Set([
      "trabzon", "muscat", "amman", "bali", "colombo", "zanzibar",
      "capetown", "mauritius", "auckland"
    ]);
    const driverDestinations = new Set(["cairo"]);
    const resortDestinations = new Set(["maldives", "cancun"]);

    destination.move = driverDestinations.has(destination.id)
      ? "driver"
      : resortDestinations.has(destination.id)
        ? "resort"
        : carDestinations.has(destination.id)
          ? "car"
          : "public";
  }

  if (!Array.isArray(destination.tags)) destination.tags = [];
  if (!Array.isArray(destination.good)) destination.good = [];
});
