document.addEventListener("DOMContentLoaded", function () {
    const searchBar = document.getElementById("searchBar");
    const tableBody = document.getElementById("transactionsTable");
    const originalRows = [...tableBody.querySelectorAll("tr")];

    function getMinRows() {
        const rowHeight = 40; // in pixels
        const tableContainer = document.querySelector(".table-container");
        const availableHeight = window.innerHeight * 0.65; // 70% of viewport height
        return Math.floor(availableHeight / rowHeight); // Calculation of minimum rows to display. Variable depending on the screen size.
    }

    // Main function to fill out table
    function filterTable(query) {
        // Filter rows based on search
        let visibleCount = 0;
        originalRows.forEach(row => {
            const match = row.innerText.toLowerCase().includes(query.toLowerCase());
            row.style.display = match ? "" : "none";
            if (match) visibleCount++;
        });

        // Removes existing placeholder rows upon refresh
        tableBody.querySelectorAll(".placeholder-row").forEach(row => row.remove());

        // Adds placeholder rows
        const minRows = getMinRows();
        const rowsToAdd = Math.max(0, minRows - visibleCount);
        for (let i = 0; i < rowsToAdd; i++) {
            const placeholder = document.createElement("tr");
            placeholder.classList.add("placeholder-row");
            placeholder.innerHTML = `<td colspan="7" style="height: 40px;"></td>`;
            tableBody.appendChild(placeholder);
        }
    }

    filterTable("");

    searchBar.addEventListener("input", function () {
        filterTable(this.value);
    });

    window.addEventListener("resize", function () {
        filterTable(searchBar.value);
    });
});
