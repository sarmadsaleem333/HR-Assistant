document.getElementById("rankForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const zip = document.getElementById("zip").files[0];
  const config = document.getElementById("config").value;
  const mappings = document.getElementById("mappings").value;

  const formData = new FormData();
  formData.append("cvs_zip", zip);
  formData.append("config", config);
  formData.append("mappings", mappings);

  document.getElementById("results").classList.add("hidden");

  try {
    const res = await fetch("/rank", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    const rankingDiv = document.getElementById("ranking");
    rankingDiv.innerHTML = "";

    data.ranked_candidates.forEach((c, idx) => {
      const card = document.createElement("div");
      card.className = "rank-card";

      const badge = document.createElement("div");
      badge.className = "rank-badge";
      badge.textContent = idx + 1;

      card.innerHTML = `
        <h3>${c.name}</h3>
        <div class="score">Score: ${c.sys_score}</div>
      `;

      card.appendChild(badge);
      rankingDiv.appendChild(card);
    });

    document.getElementById("explanation").textContent =
      data.explanation || "No explanation available.";

    document.getElementById("results").classList.remove("hidden");
  } catch (err) {
    alert("Error processing CVs");
    console.error(err);
  }
});
