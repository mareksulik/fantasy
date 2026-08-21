// Fantasy Vuelta rider scraper
// Run in the browser console on https://fantasybytissot.lavuelta.es (riders list page, logged in).
// Paginates through every page, de-duplicates, and downloads all_vuelta_riders.csv
// (columns: Meno jazdca, Tím, Kategória, Cena).

// Extract riders visible on the current page.
function extractRidersData() {
    let riders = [];
    document.querySelectorAll('sportif-item').forEach(item => {
        let rider = {
            name: item.querySelector('.nom-sportif')?.textContent?.trim(),
            team: item.querySelector('.club-sportif span')?.textContent?.trim(),
            category: item.querySelector('.position')?.textContent?.trim(),
            price: item.querySelector('.valeur-sportif-nb')?.textContent?.trim()
        };
        if (rider.name && rider.team && rider.category && rider.price) {
            riders.push(rider);
        }
    });
    return riders;
}

function convertToCSV(riders) {
    let csv = 'Meno jazdca,Tím,Kategória,Cena\n';
    riders.forEach(rider => {
        csv += `"${rider.name}","${rider.team}","${rider.category}","${rider.price}"\n`;
    });
    return csv;
}

// Walk every page until the "next" button is gone/disabled, or no new rider appears.
async function getAllRiders() {
    let byName = new Map();
    let page = 1;
    const maxPages = 100; // safety cap; real lists are < 40 pages

    const addCurrentPage = () => {
        let before = byName.size;
        extractRidersData().forEach(r => byName.set(`${r.name}|${r.team}`, r));
        return byName.size - before;
    };

    addCurrentPage();
    console.log(`Page ${page} - total unique riders: ${byName.size}`);

    while (page < maxPages) {
        let nextButton = document.querySelector('.mat-mdc-paginator-navigation-next');
        if (!nextButton || nextButton.disabled) break;

        nextButton.click();
        await new Promise(resolve => setTimeout(resolve, 1200)); // wait for re-render

        page++;
        let added = addCurrentPage();
        console.log(`Page ${page} - total unique riders: ${byName.size} (+${added})`);

        // Stop if a page produced nothing new (end of list / stuck paginator).
        if (added === 0) break;
    }

    return Array.from(byName.values());
}

getAllRiders().then(riders => {
    if (riders.length === 0) {
        console.error('No riders found. The page DOM selectors may have changed — ' +
            'inspect a rider card and update extractRidersData() selectors.');
        return;
    }
    console.log(`Collected ${riders.length} riders.`);
    console.table(riders);

    let csv = convertToCSV(riders);
    let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'all_vuelta_riders.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});
