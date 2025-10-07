/** @odoo-module */

import { patch } from '@web/core/utils/patch';
import { useService } from '@web/core/utils/hooks';
import { PosStore } from '@point_of_sale/app/store/pos_store';
import { ActionpadWidget } from '@point_of_sale/app/screens/product_screen/action_pad/action_pad';
import { SelectionPopup } from '@point_of_sale/app/utils/input_popups/selection_popup';
import { makeAwaitable } from '@point_of_sale/app/store/make_awaitable_dialog';

// Load occupied rooms after the POS data is processed
patch(PosStore.prototype, {
    async afterProcessServerData() {
        const res = await super.afterProcessServerData(...arguments);
        try {
            this.occupied_rooms = await this.data.call('pos.order', 'get_occupied_rooms', []);
        } catch (error) {
            console.error('pos_to_hotel_folio: failed to load occupied rooms', error);
            this.occupied_rooms = [];
        }
        return res;
    },
    async pay() {
        // Intercept the default payment flow in restaurant mode
        if (this.config?.module_pos_restaurant) {
            await this.sendCurrentOrderToFolio();
            return;
        }
        return await super.pay(...arguments);
    },
    async sendCurrentOrderToFolio() {
        const order = this.get_order();
        if (!order || order.lines.length === 0 || order.finalized) {
            return;
        }
        try {
            await this.syncAllOrders({ orders: [order] });
        } catch (e) {
            // ignore
        }
        const rooms = this.occupied_rooms || [];
        if (!rooms.length) {
            this.notification.add('No occupied rooms with active folios', { type: 'warning' });
            return;
        }
        const list = rooms.map((r) => ({ id: r.id, label: r.name, item: r }));
        const selectedRoom = await makeAwaitable(this.dialog, SelectionPopup, {
            title: 'Select Occupied Room',
            list,
        });
        if (!selectedRoom) {
            return;
        }
        try {
            await this.data.write('pos.order', [order.id], { room_id: selectedRoom.id });
            await this.data.call('pos.order', 'action_send_to_folio', [[order.id]]);
            this.notification.add('Order sent to room folio', { type: 'success' });
            this.removeOrder(order);
            this.add_new_order();
        } catch (error) {
            console.error('pos_to_hotel_folio: send to folio failed', error);
            this.notification.add('Failed to send to folio. Please try again.', { type: 'danger' });
        }
    },
});

// Add a Send-to-Folio action on the Action pad (replaces Payment button via XML)
patch(ActionpadWidget.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService('dialog');
        this.notification = useService('notification');
    },
    async onClickSendToFolio() {
        await this.pos.sendCurrentOrderToFolio();
    },
});