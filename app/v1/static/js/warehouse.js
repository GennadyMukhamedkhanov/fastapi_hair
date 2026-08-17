// ============================================
// ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ
// ============================================

// products объявлен в HTML через Jinja2
let warehouseData = {};

const API = {
    getData: '/v1/warehouse/data',
    saveRow: '/v1/warehouse/save',
    saveAll: '/v1/warehouse/save-all',
};

// ============================================
// ЗАГРУЗКА ДАННЫХ ИЗ REDIS
// ============================================

async function loadWarehouseData() {
    try {
        const response = await fetch(API.getData);
        if (response.ok) {
            warehouseData = await response.json();
            console.log('✅ Данные складов загружены из Redis:', warehouseData);
        } else {
            warehouseData = {};
        }
    } catch (error) {
        console.warn('⚠️ Не удалось загрузить данные складов:', error);
        warehouseData = {};
    }
    renderTable();
}

// ============================================
// ОТРИСОВКА ТАБЛИЦЫ
// ============================================

function renderTable() {
    const tbody = document.getElementById('table-body');

    if (typeof products === 'undefined' || !products || products.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" style="text-align: center; padding: 40px; color: #6b7280;">
                    <div class="empty-state">
                        <span class="icon">📭</span>
                        <div class="title">Нет товаров для сверки</div>
                        <div class="subtitle">Добавьте товары на склад или обновите страницу</div>
                    </div>
                </td>
            </tr>
        `;
        updateTotals(0, 0, 0, 0, 0, true);
        return;
    }

    let totalStock = 0;
    let totalDmitrieva = 0;
    let totalZelenaya = 0;
    let totalSum = 0;
    let mismatchCount = 0;

    tbody.innerHTML = '';

    products.forEach((product) => {
        const id = product.id;
        const tone = product.tone?.tone || '—';
        const length_cm = product.length_cm || 0;
        const stock = product.stock_grams || 0;

        const dmitrieva = warehouseData[id]?.dmitrieva ?? 0;
        const zelenaya = warehouseData[id]?.zelenaya ?? 0;
        const sum = dmitrieva + zelenaya;
        const isMatch = sum === stock;

        totalStock += stock;
        totalDmitrieva += dmitrieva;
        totalZelenaya += zelenaya;
        totalSum += sum;
        if (!isMatch) mismatchCount++;

        const tr = document.createElement('tr');
        tr.id = `product-row-${id}`;
        tr.innerHTML = `
            <td data-label="Тон">${tone}</td>
            <td data-label="Длина">${length_cm} см</td>
            <td data-label="Остаток">${stock} г</td>
            <td data-label="Склад Дмитриева">
                <input type="number"
                       class="stock-input ${isMatch ? 'match' : 'mismatch'}"
                       id="dmitrieva-${id}"
                       data-id="${id}"
                       data-warehouse="dmitrieva"
                       value="${dmitrieva}"
                       min="0"
                       inputmode="numeric"
                       onfocus="this.select()"
                       oninput="onInputChange(${id}, 'dmitrieva', this.value)">
            </td>
            <td data-label="Склад Зеленая">
                <input type="number"
                       class="stock-input ${isMatch ? 'match' : 'mismatch'}"
                       id="zelenaya-${id}"
                       data-id="${id}"
                       data-warehouse="zelenaya"
                       value="${zelenaya}"
                       min="0"
                       inputmode="numeric"
                       onfocus="this.select()"
                       oninput="onInputChange(${id}, 'zelenaya', this.value)">
            </td>
            <td data-label="Сумма" id="sum-${id}">${sum} г</td>
            <td data-label="Статус" id="status-${id}">
                <span class="mismatch-badge ${isMatch ? 'success' : 'error'}">
                    ${isMatch ? '✅ Совпадает' : '❌ Не совпадает'}
                </span>
            </td>
            <td data-label="Действия">
                <button class="btn-sm btn-save" onclick="saveRow(${id})">💾 Сохранить</button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    updateTotals(totalStock, totalDmitrieva, totalZelenaya, totalSum, mismatchCount, totalSum === totalStock);
}

// ============================================
// ОБНОВЛЕНИЕ ОДНОЙ СТРОКИ (БЕЗ ПЕРЕРИСОВКИ)
// ============================================

function updateRow(productId) {
    const product = products.find(p => p.id === productId);
    if (!product) return;

    const stock = product.stock_grams || 0;
    const dmitrieva = warehouseData[productId]?.dmitrieva ?? 0;
    const zelenaya = warehouseData[productId]?.zelenaya ?? 0;
    const sum = dmitrieva + zelenaya;
    const isMatch = sum === stock;

    const dmitrievaInput = document.getElementById(`dmitrieva-${productId}`);
    const zelenayaInput = document.getElementById(`zelenaya-${productId}`);
    const sumCell = document.getElementById(`sum-${productId}`);
    const statusCell = document.getElementById(`status-${productId}`);

    if (dmitrievaInput) {
        dmitrievaInput.className = `stock-input ${isMatch ? 'match' : 'mismatch'}`;
    }
    if (zelenayaInput) {
        zelenayaInput.className = `stock-input ${isMatch ? 'match' : 'mismatch'}`;
    }
    if (sumCell) {
        sumCell.textContent = `${sum} г`;
    }
    if (statusCell) {
        statusCell.innerHTML = `
            <span class="mismatch-badge ${isMatch ? 'success' : 'error'}">
                ${isMatch ? '✅ Совпадает' : '❌ Не совпадает'}
            </span>
        `;
    }

    recalculateTotals();
}

// ============================================
// ПЕРЕСЧЕТ ИТОГОВ
// ============================================

function recalculateTotals() {
    let totalStock = 0;
    let totalDmitrieva = 0;
    let totalZelenaya = 0;
    let totalSum = 0;
    let mismatchCount = 0;

    products.forEach((product) => {
        const id = product.id;
        const stock = product.stock_grams || 0;
        const dmitrieva = warehouseData[id]?.dmitrieva ?? 0;
        const zelenaya = warehouseData[id]?.zelenaya ?? 0;
        const sum = dmitrieva + zelenaya;

        totalStock += stock;
        totalDmitrieva += dmitrieva;
        totalZelenaya += zelenaya;
        totalSum += sum;
        if (sum !== stock) mismatchCount++;
    });

    const totalMatch = totalSum === totalStock;
    updateTotals(totalStock, totalDmitrieva, totalZelenaya, totalSum, mismatchCount, totalMatch);
}

// ============================================
// ОБНОВЛЕНИЕ ИТОГОВ
// ============================================

function updateTotals(totalStock, totalDmitrieva, totalZelenaya, totalSum, mismatchCount, totalMatch) {
    const productCount = typeof products !== 'undefined' && products ? products.length : 0;

    document.getElementById('total-products').textContent = productCount;
    document.getElementById('total-stock').textContent = totalStock + ' г';
    document.getElementById('total-dmitrieva').textContent = totalDmitrieva + ' г';
    document.getElementById('total-zelenaya').textContent = totalZelenaya + ' г';
    document.getElementById('total-stock-footer').textContent = totalStock + ' г';
    document.getElementById('total-dmitrieva-footer').textContent = totalDmitrieva + ' г';
    document.getElementById('total-zelenaya-footer').textContent = totalZelenaya + ' г';
    document.getElementById('total-sum-footer').textContent = totalSum + ' г';

    const statusBadge = document.getElementById('status-badge');
    if (productCount === 0) {
        statusBadge.textContent = '⏳ Нет данных';
        statusBadge.style.color = '#6b7280';
    } else if (totalMatch && mismatchCount === 0) {
        statusBadge.textContent = '✅ Совпадает';
        statusBadge.style.color = '#22c55e';
    } else {
        statusBadge.textContent = `❌ Не совпадает (${mismatchCount} позиций)`;
        statusBadge.style.color = '#ef4444';
    }

    document.getElementById('total-status-footer').textContent =
        productCount === 0 ? '—' : (totalMatch ? '✅' : '❌');
}

// ============================================
// ОБРАБОТКА ИЗМЕНЕНИЙ В ПОЛЯХ
// ============================================

function onInputChange(productId, warehouse, value) {
    const numValue = parseInt(value) || 0;
    if (!warehouseData[productId]) {
        warehouseData[productId] = {};
    }
    warehouseData[productId][warehouse] = numValue;
    updateRow(productId);
}

// ============================================
// СОХРАНЕНИЕ ОДНОЙ ПОЗИЦИИ В REDIS
// ============================================

async function saveRow(productId) {
    const data = warehouseData[productId] || {};

    if (!data.dmitrieva && !data.zelenaya) {
        showToast('⚠️ Нет данных для сохранения', 'error');
        return;
    }

    try {
        const response = await fetch(API.saveRow, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                dmitrieva: data.dmitrieva || 0,
                zelenaya: data.zelenaya || 0
            })
        });

        if (response.ok) {
            showToast(`✅ Данные для товара #${productId} сохранены`, 'success');
            await loadWarehouseData();
        } else {
            showToast('❌ Ошибка сохранения', 'error');
        }
    } catch (error) {
        showToast('❌ Ошибка сети', 'error');
    }
}

// ============================================
// СОХРАНЕНИЕ ВСЕХ ДАННЫХ В REDIS
// ============================================

async function saveAll() {
    const hasData = Object.values(warehouseData).some(
        item => item.dmitrieva > 0 || item.zelenaya > 0
    );

    if (!hasData) {
        showToast('⚠️ Нет данных для сохранения', 'error');
        return;
    }

    try {
        const response = await fetch(API.saveAll, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(warehouseData)
        });

        if (response.ok) {
            showToast(`✅ Все данные сохранены (${Object.keys(warehouseData).length} позиций)`, 'success');
            await loadWarehouseData();
        } else {
            showToast('❌ Ошибка сохранения', 'error');
        }
    } catch (error) {
        showToast('❌ Ошибка сети', 'error');
    }
}

// ============================================
// СБРОС ВСЕХ ДАННЫХ
// ============================================

async function resetAll() {
    if (!confirm('Вы уверены, что хотите сбросить ВСЕ данные складов?')) {
        return;
    }

    warehouseData = {};

    try {
        const response = await fetch(API.saveAll, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({})
        });
        if (response.ok) {
            showToast('🔄 Все данные сброшены', 'success');
            await loadWarehouseData();
        } else {
            showToast('❌ Ошибка сброса', 'error');
        }
    } catch (error) {
        showToast('❌ Ошибка сети', 'error');
    }
}

// ============================================
// TOAST
// ============================================

function showToast(message, type = 'success') {
    document.querySelectorAll('.toast').forEach(el => el.remove());

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    requestAnimationFrame(() => toast.classList.add('show'));

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ============================================
// ИНИЦИАЛИЗАЦИЯ
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Загрузка страницы сверки складов...');
    loadWarehouseData();
});