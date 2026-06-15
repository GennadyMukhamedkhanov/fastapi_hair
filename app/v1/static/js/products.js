// Функция для генерации цвета на основе названия тона
function getColorForTone(tone) {
    if (!tone || tone === 'none') return '#ffffff';

    // Числовые тона 1.0 - 10.0 с контрастными цветами
    const numericColors = {
        '1.0': '#FFB3BA', // светло-розовый
        '2.0': '#FFD4B3', // персиковый
        '3.0': '#FFE6B3', // светло-желтый
        '4.0': '#FFFFB3', // лимонный
        '5.0': '#D4FFB3', // салатовый
        '6.0': '#B3FFD4', // мятный
        '7.0': '#B3E6FF', // голубой
        '8.0': '#B3CCFF', // васильковый
        '9.0': '#CCB3FF', // сиреневый
        '10.0': '#E6B3FF'  // лавандовый
    };

    if (numericColors[tone]) {
        return numericColors[tone];
    }

    // Для тонов ОВ с разными яркими оттенками
    const ovMatch = tone.match(/ОВ\s*(\d+)\/(\d+)/);
    if (ovMatch) {
        const num = parseInt(ovMatch[1]);
        const colors = {
            1: '#FFB3BA',  // нежно-розовый
            2: '#FFCCB3',  // коралловый
            3: '#FFE0B3',  // шафрановый
            4: '#FFF0B3',  // кремовый
            5: '#D4F0B3',  // фисташковый
            6: '#B3F0D4',  // изумрудный
            7: '#B3E0F0',  // бирюзовый
            8: '#B3CCF0',  // небесный
            9: '#CCB3F0',  // фиолетовый
            10: '#E6B3F0'  // орхидея
        };
        return colors[num] || '#F0D4B3';
    }

    // Для тонов с префиксом NB (натуральные)
    const nbMatch = tone.match(/NB\s*(\d+)\/(\d+)/i);
    if (nbMatch) {
        const num = parseInt(nbMatch[1]);
        const colors = {
            1: '#F5E6D3',  // светло-бежевый
            2: '#EDD9C4',  // бежевый
            3: '#E5CCB5',  // песочный
            4: '#DDBFA6',  // карамельный
            5: '#D5B297',  // кофейный
            6: '#CDA588',  // шоколадный
            7: '#C59879',  // темный шоколад
            8: '#BD8B6A',  // коричневый
            9: '#B57E5B',  // древесный
            10: '#AD714C'   // махагон
        };
        return colors[num] || '#E8D5C4';
    }

    // Для тонов с префиксом GB (пепельные)
    const gbMatch = tone.match(/GB\s*(\d+)\/(\d+)/i);
    if (gbMatch) {
        const num = parseInt(gbMatch[1]);
        const colors = {
            1: '#E6E6F0',  // светло-пепельный
            2: '#D9D9E6',  // пепельный
            3: '#CCCCDB',  // серебристый
            4: '#BFBFD1',  // серо-голубой
            5: '#B2B2C6',  // стальной
            6: '#A5A5BC',  // грифельный
            7: '#9999B1',  // серо-синий
            8: '#8C8CA6',  // дымчатый
            9: '#7F7F9C',  // мокрый асфальт
            10: '#727291'   // графитовый
        };
        return colors[num] || '#D9D9E6';
    }

    // Для тонов с префиксом RB (красноватые)
    const rbMatch = tone.match(/RB\s*(\d+)\/(\d+)/i);
    if (rbMatch) {
        const num = parseInt(rbMatch[1]);
        const colors = {
            1: '#FFD4D4',  // нежно-розовый
            2: '#FFC4C4',  // розовый
            3: '#FFB4B4',  // лососевый
            4: '#FFA4A4',  // коралловый
            5: '#FF9494',  // алый
            6: '#FF8484',  // красный
            7: '#E67373',  // терракотовый
            8: '#CC6363',  // кирпичный
            9: '#B35252',  // бордовый
            10: '#994242'   // винный
        };
        return colors[num] || '#FFD4D4';
    }

    // Генерация цвета на основе хеша с более насыщенными оттенками
    let hash = 0;
    for (let i = 0; i < tone.length; i++) {
        hash = ((hash << 5) - hash) + tone.charCodeAt(i);
        hash |= 0;
    }
    // Используем более насыщенные цвета (70% насыщенность, 85% яркость)
    const hue = Math.abs(hash % 360);
    return `hsl(${hue}, 75%, 85%)`;
}

// Применяем цвета ко всем строкам при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const rows = document.querySelectorAll('.product-row');

    rows.forEach(row => {
        const tone = row.getAttribute('data-tone');
        const color = getColorForTone(tone);

        // Применяем цвет фона к строке
        row.style.backgroundColor = color;

        // Применяем ко всем ячейкам строки
        const cells = row.querySelectorAll('td');
        cells.forEach(cell => {
            cell.style.backgroundColor = color;
        });
    });
});