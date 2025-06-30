// 1. Najprv definujeme všetky potrebné funkcie

// Funkcia na extrahovanie dát z aktuálnej stránky
function extractRidersData() {
    let riders = [];
    document.querySelectorAll('sportif-item').forEach(item => {
        let rider = {
            name: item.querySelector('.nom-sportif')?.textContent?.trim(),
            team: item.querySelector('.club-sportif span')?.textContent?.trim(),
            category: item.querySelector('.position')?.textContent?.trim(),
            price: item.querySelector('.valeur-sportif-nb')?.textContent?.trim()
        };
        // Pridáme len ak máme všetky údaje
        if (rider.name && rider.team && rider.category && rider.price) {
            riders.push(rider);
        }
    });
    return riders;
}

// Funkcia na konverziu do CSV
function convertToCSV(riders) {
    // Hlavička
    let csv = 'Meno jazdca,Tím,Kategória,Cena\n';
    
    // Dáta
    riders.forEach(rider => {
        csv += `"${rider.name}","${rider.team}","${rider.category}","${rider.price}"\n`;
    });
    
    return csv;
}

// Funkcia na získanie všetkých jazdcov zo všetkých stránok
async function getAllRiders() {
    let allRiders = [];
    let nextButton = document.querySelector('.mat-mdc-paginator-navigation-next');
    let currentPage = 1;
    let totalPages = Math.ceil(261 / 10); // 261 jazdcov, 10 na stránku
    
    // Získať dáta z prvej stránky
    allRiders = allRiders.concat(extractRidersData());
    console.log(`Stránka ${currentPage}/${totalPages} - Získaných: ${allRiders.length} jazdcov`);
    
    // Prejsť všetky ostatné stránky
    while (nextButton && !nextButton.disabled && currentPage < totalPages) {
        nextButton.click();
        
        // Počkať na načítanie novej stránky
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        currentPage++;
        allRiders = allRiders.concat(extractRidersData());
        console.log(`Stránka ${currentPage}/${totalPages} - Získaných: ${allRiders.length} jazdcov`);
        
        // Znovu nájsť tlačidlo (môže sa obnoviť v DOM)
        nextButton = document.querySelector('.mat-mdc-paginator-navigation-next');
    }
    
    return allRiders;
}

// 2. Teraz spustíme získavanie všetkých dát
getAllRiders().then(riders => {
    console.log(`Celkovo získaných: ${riders.length} jazdcov`);
    console.table(riders);
    
    // Export do CSV
    let csv = convertToCSV(riders);
    let blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    let link = document.createElement('a');
    let url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'all_tour_de_france_riders.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});