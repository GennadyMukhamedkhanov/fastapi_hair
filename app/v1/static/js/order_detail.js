// order_detail.js - ПОЛНАЯ ВЕРСИЯ

document.addEventListener('DOMContentLoaded', function () {
    const statusSelect = document.getElementById('orderStatusSelect');
    const deleteOrderButton = document.getElementById('deleteOrderButton');
    
    // Функция для показа уведомлений
    function showNotification(message, type = 'info') {
        let notificationContainer = document.querySelector('.notification-container');
        if (!notificationContainer) {
            notificationContainer = document.createElement('div');
            notificationContainer.className = 'notification-container';
            document.body.appendChild(notificationContainer);
        }
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-icon">${type === 'warning' ? '⚠️' : 'ℹ️'}</span>
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close">×</button>
        `;
        
        notificationContainer.appendChild(notification);
        
        setTimeout(() => notification.classList.add('show'), 10);
        
        const closeBtn = notification.querySelector('.notification-close');
        closeBtn.addEventListener('click', () => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        });
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.classList.remove('show');
                setTimeout(() => notification.remove(), 300);
            }
        }, 5000);
    }
    
    // Функция для экранирования HTML
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    // Проверяем flash сообщения из cookies
    function checkFlashMessages() {
        const cookies = document.cookie.split(';');
        cookies.forEach(cookie => {
            const [name, value] = cookie.trim().split('=');
            if (name === 'order_deleted' && value === 'true') {
                showNotification('Заказ успешно удален', 'info');
                document.cookie = 'order_deleted=; max-age=0; path=/';
            } else if (name === 'delete_error') {
                showNotification(`Ошибка при удалении: ${decodeURIComponent(value)}`, 'warning');
                document.cookie = 'delete_error=; max-age=0; path=/';
            }
        });
    }
    
    // Проверяем, удален ли заказ
    const isOrderDeleted = document.querySelector('.deleted-order-banner') !== null;
    
    if (isOrderDeleted) {
        if (statusSelect) {
            statusSelect.disabled = true;
            statusSelect.title = "Невозможно изменить статус удаленного заказа";
        }
        
        if (deleteOrderButton) {
            deleteOrderButton.style.display = 'none';
        }
        
        showNotification('Этот заказ был удален и не может быть изменен', 'warning');
    }
    
    checkFlashMessages();
    
    // Функция для подсчёта итоговых сумм
    function calculateTotals() {
        const tableRows = document.querySelectorAll('.order-detail-table tbody tr');
        const dataRows = Array.from(tableRows).filter(row => !row.classList.contains('total-row'));

        let totalPurchasePrice = 0;
        let totalSalePrice = 0;
        let totalProfit = 0;

        dataRows.forEach(row => {
            const purchasePriceCell = row.querySelector('.purchase-price-cell');
            const salePriceCell = row.querySelector('.sale-price-cell');
            const profitCell = row.querySelector('.profit-cell');

            if (purchasePriceCell && salePriceCell && profitCell) {
                const purchaseText = purchasePriceCell.textContent.replace(' ₽', '').replace(',', '.').trim();
                const saleText = salePriceCell.textContent.replace(' ₽', '').replace(',', '.').trim();
                const profitText = profitCell.textContent.replace(' ₽', '').replace(',', '.').trim();

                const purchaseValue = parseFloat(purchaseText);
                const saleValue = parseFloat(saleText);
                const profitValue = parseFloat(profitText);

                if (!isNaN(purchaseValue)) totalPurchasePrice += purchaseValue;
                if (!isNaN(saleValue)) totalSalePrice += saleValue;
                if (!isNaN(profitValue)) totalProfit += profitValue;
            }
        });

        const totalPurchaseElement = document.getElementById('totalPurchasePrice');
        const totalSaleElement = document.getElementById('totalSalePrice');
        const totalProfitElement = document.getElementById('totalProfit');

        if (totalPurchaseElement) {
            totalPurchaseElement.textContent = totalPurchasePrice.toFixed(2) + ' ₽';
        }
        if (totalSaleElement) {
            totalSaleElement.textContent = totalSalePrice.toFixed(2) + ' ₽';
        }
        if (totalProfitElement) {
            totalProfitElement.textContent = totalProfit.toFixed(2) + ' ₽';
        }
    }

    calculateTotals();

    if (!statusSelect || isOrderDeleted) return;

    let originalStatus = statusSelect.value;
    let pendingNewStatus = null;
    let isUpdating = false;
    let modalInstance = null;

    // Получение товаров из таблицы с реальными ID и ценами
    function getOrderItems() {
        const items = [];
        const rows = document.querySelectorAll('.order-detail-table tbody tr:not(.total-row)');

        rows.forEach((row) => {
            const itemId = row.dataset.itemId;
            const productNameCell = row.cells[0];
            const productName = productNameCell ? productNameCell.textContent.trim() : '';
            const gramsCell = row.querySelector('.grams-cell');
            const grams = gramsCell ? parseInt(gramsCell.textContent.replace(' г', '')) : 0;

            const purchasePriceCell = row.querySelector('.purchase-price-cell');
            const purchasePricePer100g = purchasePriceCell ? parseFloat(purchasePriceCell.textContent.replace(' ₽', '').replace(',', '.')) : 0;

            const salePriceCell = row.querySelector('.sale-price-cell');
            const salePricePer100g = salePriceCell ? parseFloat(salePriceCell.textContent.replace(' ₽', '').replace(',', '.')) : 0;

            items.push({
                id: itemId,
                name: productName,
                grams: grams,
                purchase_price_per_100g: purchasePricePer100g,
                sale_price_per_100g: salePricePer100g
            });
        });

        return items;
    }

    // Модальное окно для ввода цен продажи
    function showSalePricesModal(onConfirm) {
        const items = getOrderItems();

        if (items.length === 0) {
            showStatusMessage('Нет товаров для установки цен', 'error');
            return false;
        }

        removeExistingModal();

        const modal = document.createElement('div');
        modal.className = 'sale-prices-modal';
        modal.innerHTML = `
            <div class="sale-prices-overlay"></div>
            <div class="sale-prices-dialog">
                <div class="sale-prices-header">
                    <h3>Установка цен продажи</h3>
                    <p style="margin: 8px 0 0 0; font-size: 14px; opacity: 0.9;">Для подтверждения статуса "Доставлен"</p>
                </div>
                <div class="sale-prices-body">
                    <p class="sale-prices-text">Введите цену продажи для каждого товара:</p>
                    <div class="sale-prices-form">
                        ${items.map((item) => {
                            const suggestedTotalPrice = item.sale_price_per_100g && item.sale_price_per_100g > 0
                                ? (item.grams * item.sale_price_per_100g / 100).toFixed(2)
                                : '';
                            return `
                                <div class="sale-price-item" data-item-id="${item.id}" data-grams="${item.grams}">
                                    <div class="sale-price-item-label">
                                        <strong>${escapeHtml(item.name)}</strong>
                                        <div style="font-size: 12px; color: #888; margin-top: 4px;">
                                            Вес: ${item.grams} г (${(item.grams/1000).toFixed(3)} кг)
                                        </div>
                                        <div style="font-size: 11px; color: #999; margin-top: 2px;">
                                            Закупочная цена: ${item.purchase_price_per_100g.toFixed(2)} ₽/100г
                                        </div>
                                    </div>
                                    <div class="sale-price-item-input-wrapper">
                                        <input type="number"
                                               class="sale-price-item-input"
                                               data-item-id="${item.id}"
                                               placeholder="Цена продажи (за позицию)"
                                               step="0.01"
                                               min="0"
                                               value="${suggestedTotalPrice}"
                                               style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                                        <span class="sale-price-item-unit">₽/позиция</span>
                                    </div>
                                    <div style="margin-top: 8px; padding: 6px; background: #f5f5f5; border-radius: 4px; font-size: 12px;">
                                        <span>💰 Итого за позицию: </span>
                                        <strong class="item-total-price">0 ₽</strong>
                                        <span style="font-size: 11px; color: #666; margin-left: 8px;">
                                            (эквивалент: <span class="item-price-per-100g">0</span> ₽/100г)
                                        </span>
                                    </div>
                                </div>
                            `;
                        }).join('')}
                    </div>
                </div>
                <div class="sale-prices-actions">
                    <button type="button" class="btn-cancel-prices">Отмена</button>
                    <button type="button" class="btn-confirm-prices">Подтвердить</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        document.body.classList.add('modal-open');

        function updateAllPrices() {
            const priceInputs = modal.querySelectorAll('.sale-price-item-input');
            priceInputs.forEach(input => {
                const pricePerUnit = parseFloat(input.value) || 0;
                const itemDiv = input.closest('.sale-price-item');
                const grams = parseInt(itemDiv.dataset.grams);

                const pricePer100g = grams > 0 ? (pricePerUnit / grams * 100).toFixed(2) : '0.00';

                const totalPriceSpan = itemDiv.querySelector('.item-total-price');
                const pricePer100gSpan = itemDiv.querySelector('.item-price-per-100g');

                if (totalPriceSpan) totalPriceSpan.textContent = pricePerUnit.toFixed(2);
                if (pricePer100gSpan) pricePer100gSpan.textContent = pricePer100g;
            });
        }

        const priceInputs = modal.querySelectorAll('.sale-price-item-input');
        priceInputs.forEach(input => {
            input.addEventListener('input', function() {
                const pricePerUnit = parseFloat(this.value) || 0;
                const itemDiv = this.closest('.sale-price-item');
                const grams = parseInt(itemDiv.dataset.grams);

                const pricePer100g = grams > 0 ? (pricePerUnit / grams * 100).toFixed(2) : '0.00';

                const totalPriceSpan = itemDiv.querySelector('.item-total-price');
                const pricePer100gSpan = itemDiv.querySelector('.item-price-per-100g');

                if (totalPriceSpan) totalPriceSpan.textContent = pricePerUnit.toFixed(2);
                if (pricePer100gSpan) pricePer100gSpan.textContent = pricePer100g;
            });
        });

        updateAllPrices();

        const overlay = modal.querySelector('.sale-prices-overlay');
        const cancelBtn = modal.querySelector('.btn-cancel-prices');
        const confirmBtn = modal.querySelector('.btn-confirm-prices');

        function cleanup() {
            if (modal && modal.parentNode) {
                modal.remove();
            }
            document.body.classList.remove('modal-open');
        }

        function handleCancel() {
            cleanup();
            if (statusSelect && originalStatus) {
                statusSelect.value = originalStatus;
            }
        }

        function handleConfirm() {
            const salePrices = {};
            const priceInputs = modal.querySelectorAll('.sale-price-item-input');

            let hasValidPrices = true;
            priceInputs.forEach((input) => {
                const itemId = input.dataset.itemId;
                const price = parseFloat(input.value);

                if (itemId !== undefined) {
                    if (isNaN(price) || price <= 0) {
                        hasValidPrices = false;
                        input.style.borderColor = 'red';
                        input.style.borderWidth = '2px';
                    } else {
                        input.style.borderColor = '#ddd';
                        input.style.borderWidth = '1px';
                        salePrices[itemId] = price;
                    }
                }
            });

            if (!hasValidPrices) {
                showStatusMessage('Пожалуйста, укажите корректную цену продажи для всех товаров (больше 0)', 'error');
                return;
            }

            cleanup();
            if (onConfirm && typeof onConfirm === 'function') {
                onConfirm(salePrices);
            }
        }

        if (overlay) overlay.addEventListener('click', handleCancel);
        if (cancelBtn) cancelBtn.addEventListener('click', handleCancel);
        if (confirmBtn) confirmBtn.addEventListener('click', handleConfirm);

        function handleEscape(event) {
            if (event.key === 'Escape') {
                handleCancel();
            }
        }
        document.addEventListener('keydown', handleEscape);

        modal._escapeHandler = handleEscape;

        setTimeout(() => {
            const firstInput = modal.querySelector('.sale-price-item-input');
            if (firstInput) firstInput.focus();
        }, 100);

        return true;
    }

    statusSelect.addEventListener('change', function () {
        if (isUpdating) {
            statusSelect.value = originalStatus;
            return;
        }

        const newStatus = this.value;

        if (newStatus === originalStatus) {
            return;
        }

        pendingNewStatus = newStatus;

        if (newStatus === 'delivered') {
            statusSelect.value = originalStatus;
            showSalePricesModal(async (salePrices) => {
                await handleStatusChange('delivered', salePrices);
            });
            return;
        }

        showStatusConfirmationModal(newStatus);
        statusSelect.value = originalStatus;
    });

    if (deleteOrderButton && !isOrderDeleted) {
        deleteOrderButton.addEventListener('click', function (event) {
            event.preventDefault();
            if (isUpdating) return;
            showDeleteConfirmationModal();
        });
    }

    function showStatusConfirmationModal(status) {
        removeExistingModal();

        const modal = document.createElement('div');
        modal.className = 'status-confirm-modal';
        modal.innerHTML = `
            <div class="status-confirm-overlay"></div>
            <div class="status-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="statusConfirmTitle">
                <div class="status-confirm-header">
                    <h3 id="statusConfirmTitle">Подтверждение изменения статуса</h3>
                </div>
                <div class="status-confirm-body">
                    <p class="status-confirm-text">Вы хотите сменить статус заказа?</p>
                    <div class="status-preview">
                        <span class="status-label">Новый статус</span>
                        <span class="status-value">${getStatusLabel(status)}</span>
                    </div>
                </div>
                <div class="status-confirm-actions">
                    <button type="button" class="btn-cancel">Нет</button>
                    <button type="button" class="btn-confirm">Да</button>
                </div>
            </div>
        `;

        modalInstance = modal;

        bindModalEvents(modal, {
            onCancel: () => {
                modalInstance = null;
                pendingNewStatus = null;
                statusSelect.value = originalStatus;
            },
            onConfirm: () => {
                if (!pendingNewStatus) return;
                handleStatusChange(pendingNewStatus, null);
                modalInstance = null;
            }
        });
    }

    function showDeleteConfirmationModal() {
        removeExistingModal();

        const modal = document.createElement('div');
        modal.className = 'status-confirm-modal';
        modal.innerHTML = `
            <div class="status-confirm-overlay"></div>
            <div class="status-confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="deleteConfirmTitle">
                <div class="status-confirm-header">
                    <h3 id="deleteConfirmTitle">Подтверждение удаления</h3>
                </div>
                <div class="status-confirm-body">
                    <p class="status-confirm-text">Вы хотите удалить заказ?</p>
                </div>
                <div class="status-confirm-actions">
                    <button type="button" class="btn-cancel">Нет</button>
                    <button type="button" class="btn-confirm">Да</button>
                </div>
            </div>
        `;

        modalInstance = modal;

        bindModalEvents(modal, {
            onCancel: () => {
                modalInstance = null;
            },
            onConfirm: () => {
                handleDeleteOrder();
                modalInstance = null;
            }
        });
    }

    function bindModalEvents(modal, callbacks) {
        document.body.appendChild(modal);
        document.body.classList.add('modal-open');

        const overlay = modal.querySelector('.status-confirm-overlay');
        const cancelBtn = modal.querySelector('.btn-cancel');
        const confirmBtn = modal.querySelector('.btn-confirm');

        function cleanup() {
            document.body.classList.remove('modal-open');
            if (modal && modal.parentNode) {
                modal.remove();
            }
            document.removeEventListener('keydown', handleEscape);
        }

        function handleCancel() {
            if (callbacks.onCancel) callbacks.onCancel();
            cleanup();
        }

        function handleConfirm() {
            if (callbacks.onConfirm) callbacks.onConfirm();
            cleanup();
        }

        function handleEscape(event) {
            if (event.key === 'Escape') {
                handleCancel();
            }
        }

        overlay.addEventListener('click', handleCancel);
        cancelBtn.addEventListener('click', handleCancel);
        confirmBtn.addEventListener('click', handleConfirm);
        document.addEventListener('keydown', handleEscape);

        setTimeout(() => {
            confirmBtn.focus();
        }, 0);
    }

    function removeExistingModal() {
        const priceModal = document.querySelector('.sale-prices-modal');
        if (priceModal && priceModal._escapeHandler) {
            document.removeEventListener('keydown', priceModal._escapeHandler);
        }

        if (modalInstance && modalInstance.parentNode) {
            modalInstance.remove();
            modalInstance = null;
        }
        const existingModal = document.querySelector('.status-confirm-modal');
        if (existingModal) {
            existingModal.remove();
        }
        const existingPriceModal = document.querySelector('.sale-prices-modal');
        if (existingPriceModal) {
            existingPriceModal.remove();
        }
        document.body.classList.remove('modal-open');
    }

    // Функция обновления итоговых сумм из данных сервера
    function updateOrderTotals(data) {
        const totalPurchaseElement = document.getElementById('totalPurchasePrice');
        const totalSaleElement = document.getElementById('totalSalePrice');
        const totalProfitElement = document.getElementById('totalProfit');

        if (data.total_price !== undefined) {
            if (totalPurchaseElement) {
                totalPurchaseElement.textContent = parseFloat(data.total_price).toFixed(2) + ' ₽';
            }
        }

        if (data.final_price !== undefined) {
            if (totalSaleElement) {
                totalSaleElement.textContent = parseFloat(data.final_price).toFixed(2) + ' ₽';
            }
        }

        if (data.profit !== undefined) {
            if (totalProfitElement) {
                totalProfitElement.textContent = parseFloat(data.profit).toFixed(2) + ' ₽';
            }
        }

        if (data.items) {
            const rows = document.querySelectorAll('.order-detail-table tbody tr:not(.total-row)');
            rows.forEach((row, index) => {
                if (data.items[index]) {
                    const item = data.items[index];
                    const salePriceCell = row.querySelector('.sale-price-cell');
                    const profitCell = row.querySelector('.profit-cell');

                    if (salePriceCell && item.sale_total !== undefined) {
                        salePriceCell.textContent = parseFloat(item.sale_total).toFixed(2) + ' ₽';
                    }
                    if (profitCell && item.profit !== undefined) {
                        profitCell.textContent = parseFloat(item.profit).toFixed(2) + ' ₽';
                    }
                }
            });
        }
    }

    // ОСНОВНАЯ ФУНКЦИЯ ОБНОВЛЕНИЯ СТАТУСА С ИНТЕГРАЦИЕЙ updateOrderTotals
    async function handleStatusChange(newStatus, salePrices) {
        if (isUpdating) return;

        isUpdating = true;
        showStatusMessage('Обновление статуса...', 'loading');
        statusSelect.disabled = true;

        const orderId = statusSelect.dataset.orderId;
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 10000);

        const requestBody = { status: newStatus };
        if (salePrices) {
            requestBody.sale_prices = salePrices;
        }

        console.log('Отправляем данные:', requestBody);

        try {
            const response = await fetch(`/v1/orders/${orderId}/status`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });

            if (!response.ok) {
                let errorText = '';
                try {
                    const errorData = await response.json();
                    errorText = errorData.detail || errorData.message || '';
                } catch (_) {
                    errorText = '';
                }
                throw new Error(errorText || `HTTP ${response.status}`);
            }

            const data = await response.json();

            if (data.success || data.status === newStatus) {
                originalStatus = newStatus;
                statusSelect.value = newStatus;
                
                // ✅ ВАЖНО: Обновляем отображение финансов
                updateOrderTotals(data);
                
                showStatusMessage('Статус успешно обновлен!', 'success');

                setTimeout(() => {
                    location.reload();
                }, 1500);
            } else {
                throw new Error(data.message || 'Ошибка при обновлении статуса');
            }
        } catch (error) {
            console.error('Ошибка обновления статуса:', error);
            statusSelect.value = originalStatus;

            let errorMessage = 'Ошибка при обновлении статуса';
            if (error.name === 'AbortError') {
                errorMessage = 'Сервер не отвечает. Попробуйте позже.';
            } else if (error.message === 'Failed to fetch') {
                errorMessage = 'Ошибка соединения с сервером.';
            } else if (error.message) {
                errorMessage = error.message;
            }

            showStatusMessage(errorMessage, 'error');
        } finally {
            clearTimeout(timeoutId);
            isUpdating = false;
            statusSelect.disabled = false;
            setTimeout(() => {
                hideStatusMessage();
            }, 3000);
        }
    }

    async function handleDeleteOrder() {
    if (isUpdating) return;

    isUpdating = true;
    showDeleteMessage('Удаление заказа...', 'loading');

    const orderId = statusSelect?.dataset.orderId;
    if (!orderId) {
        showDeleteMessage('ID заказа не найден', 'error');
        isUpdating = false;
        return;
    }

    try {
        // Используем GET запрос как в ссылке
        const response = await fetch(`/v1/orders/delete/${orderId}`, {
            method: 'GET',  // Изменено с DELETE на GET
            headers: {
                'Content-Type': 'application/json'
            }
        });

        // GET запрос вернет редирект, нужно обработать
        if (response.redirected) {
            window.location.href = response.url;
        } else {
            const data = await response.json();
            if (data.success) {
                showDeleteMessage('Заказ успешно удален!', 'success');
                setTimeout(() => {
                    window.location.href = '/v1/orders/list';
                }, 1500);
            }
        }
    } catch (error) {
        console.error('Ошибка удаления заказа:', error);
        showDeleteMessage('Ошибка при удалении заказа', 'error');
        setTimeout(() => {
            hideDeleteMessage();
        }, 4000);
    } finally {
        isUpdating = false;
    }
}

    function showDeleteMessage(message, type) {
        const messageElement = document.querySelector('.delete-message');
        if (!messageElement) return;
        messageElement.textContent = message;
        messageElement.className = `delete-message ${type}`;
        messageElement.style.display = 'block';
    }

    function hideDeleteMessage() {
        const messageElement = document.querySelector('.delete-message');
        if (!messageElement) return;
        messageElement.style.display = 'none';
        messageElement.className = 'delete-message';
        messageElement.textContent = '';
    }

    function getStatusLabel(status) {
        const statusMap = {
            transit: 'В пути',
            delivered: 'Доставлен',
            return_transit: 'В пути (возврат)',
            returned_on_warehouse: 'Возвращен на склад'
        };
        return statusMap[status] || status;
    }

    function showStatusMessage(message, type) {
        const messageElement = document.querySelector('.status-message');
        if (!messageElement) return;
        messageElement.textContent = message;
        messageElement.className = `status-message ${type}`;
        messageElement.style.display = 'block';
    }

    function hideStatusMessage() {
        const messageElement = document.querySelector('.status-message');
        if (!messageElement) return;
        messageElement.style.display = 'none';
        messageElement.className = 'status-message';
        messageElement.textContent = '';
    }
});