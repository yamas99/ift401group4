document.addEventListener("DOMContentLoaded", function () {
    function initializeTableFiltering(searchBarId, tableId) {
        const searchBar = document.getElementById(searchBarId);
        const tableBody = document.getElementById(tableId);

        if (!searchBar || !tableBody) 
            return;

        const originalRows = [...tableBody.querySelectorAll("tr")];

        function getMinRows() {
            const rowHeight = 40; // in pixels
            const availableHeight = window.innerHeight * 0.65; // 70% of viewport height
            return Math.floor(availableHeight / rowHeight);
        }

        // Determines the number of columns in the table based on <tr> elements
        function getColumnCount() {
            const firstRow = tableBody.querySelector("tr");
            return firstRow;
        }

        // Main function to fill out table
        function filterTable(query) {
            let visibleCount = 0;
            originalRows.forEach(row => {
                const match = row.innerText.toLowerCase().includes(query.toLowerCase());
                row.style.display = match ? "" : "none";
                if (match) visibleCount++;
            });

            // Remove old placeholders
            tableBody.querySelectorAll(".placeholder-row").forEach(row => row.remove());

            // Add new placeholder rows
            const minRows = getMinRows();
            const rowsToAdd = Math.max(0, minRows - visibleCount);
            const colSpan = getColumnCount();
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
    }

    // Initialize filtering for the different tables
    initializeTableFiltering("searchBar", "usersTable");
    initializeTableFiltering("searchBar", "transactionsTable");
    initializeTableFiltering("searchBar", "stocksTable");

});
