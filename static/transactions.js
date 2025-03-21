document.addEventListener("DOMContentLoaded", function () {
    const searchBar = document.getElementById("searchBar");
    const tableBody = document.getElementById("transactionsTable");
    const originalRows = [...tableBody.querySelectorAll("tr")];
    const MIN_ROWS = 25;        // Minimum number of blank rows to show

    // Main function to fill out table
    function filterTable(query) {

        // Populates rows with data
        let visibleCount = 0;
        originalRows.forEach(row => {
            const match = row.innerText.toLowerCase().includes(query.toLowerCase());
            row.style.display = match ? "" : "none";
            if (match) visibleCount++;
        });

        // Remove existing placeholders
        tableBody.querySelectorAll(".placeholder-row").forEach(row => row.remove());

        // Adds placeholder rows
        const rowsToAdd = Math.max(0, MIN_ROWS - visibleCount);
        for (let i = 0; i < rowsToAdd; i++) {
            const placeholder = document.createElement("tr");
            placeholder.classList.add("placeholder-row");
            placeholder.innerHTML = `
                <td colspan="7" style="height: 40px;"></td>
            `;      //colspan="7" to match the number of columns in the table
            tableBody.appendChild(placeholder);
        }
    }

    filterTable("");

    // Search event, filters results upon search bar input
    searchBar.addEventListener("input", function () {
        filterTable(this.value);
    });
    
});
