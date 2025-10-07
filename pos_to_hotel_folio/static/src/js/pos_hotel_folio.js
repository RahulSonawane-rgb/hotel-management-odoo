/** @odoo-module */

import { PosStore } from '@point_of_sale/app/store/pos_store';
import { Order } from '@point_of_sale/models/order';
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';
import { SelectionPopup } from '@point_of_sale/app/utils/selection_popup/selection_popup';
import { ErrorPopup } from '@point_of_sale/app/utils/error_popup/error_popup';
import { ConfirmPopup } from '@point_of_sale/app/utils/confirm_popup/confirm_popup';
import { patch } from '@web/core/utils/patch';
import { useService } from '@web/core/utils/hooks';

// Debug to confirm JS and module loading
console.log('POS Hotel Folio JS Loaded');
console.log('Imported modules:', {
    PosStore: PosStore ? 'Loaded' : 'Undefined',
    Order: Order ? 'Loaded' : 'Undefined',
    ProductScreen: ProductScreen ? 'Loaded' : 'Undefined',
    SelectionPopup: SelectionPopup ? 'Loaded' : 'Undefined',
    ErrorPopup: ErrorPopup ? 'Loaded' : 'Undefined',
    ConfirmPopup: ConfirmPopup ? 'Loaded' : 'Undefined'
});

// Extend PosStore to load occupied rooms
patch(PosStore.prototype, {
    async after_load_server_data() {
        await super.after_load_server_data();
        try {
            this.occupied_rooms = await this.orm.call('pos.order', 'get_occupied_rooms', []);
            console.log('Occupied rooms loaded:', this.occupied_rooms);
        } catch (error) {
            console.error('Failed to load occupied rooms:', error);
        }
    }
});

// Extend Order to include room_id and sent_to_folio
patch(Order.prototype, {
    setup(values) {
        super.setup(values);
        this.room_id = this.room_id || null;
        this.sent_to_folio = this.sent_to_folio || false;
        console.log('Order setup:', { room_id: this.room_id, sent_to_folio: this.sent_to_folio });
    },
    export_as_JSON() {
        const json = super.export_as_JSON();
        json.room_id = this.room_id;
        json.sent_to_folio = this.sent_to_folio;
        return json;
    }
});

// Extend ProductScreen to replace Payment button with Send to Folio
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.popup = useService('popup');
        this.orm = useService('orm');
        console.log('ProductScreen patched');
    },
    get payButtonLabel() {
        const order = this.pos.get_order();
        return order && order.sent_to_folio ? 'Sent' : 'Send to Folio';
    },
    async onClickPay() {
        const order = this.pos.get_order();
        console.log('onClickPay called, order:', order);
        if (!order || order.get_orderlines().length === 0 || order.sent_to_folio) {
            console.log('Invalid order or already sent:', { orderlines: order?.get_orderlines().length, sent: order?.sent_to_folio });
            return;
        }
        // Ensure order is sent to kitchen (Restaurant mode)
        if (this.pos.config.is_restaurant) {
            try {
                await this.env.services.rpc({
                    model: 'pos.order',
                    method: 'send_to_kitchen',
                    args: [[order.backendId || order.name]],
                });
                console.log('Order sent to kitchen');
            } catch (error) {
                console.error('Failed to send to kitchen:', error);
            }
        }
        const roomList = this.pos.occupied_rooms.map((room) => ({
            id: room.id,
            label: room.name,
            item: room,
        }));
        console.log('Room list:', roomList);
        if (roomList.length === 0) {
            await this.popup.add(ErrorPopup, {
                title: 'No Occupied Rooms',
                body: 'No rooms with active folios available. Please check hotel bookings.',
            });
            console.log('No rooms popup shown');
            return;
        }
        const { confirmed, payload: selectedRoom } = await this.popup.add(SelectionPopup, {
            title: 'Select Occupied Room',
            list: roomList,
        });
        if (confirmed) {
            order.room_id = selectedRoom.id;
            console.log('Selected room:', selectedRoom);
            try {
                await this.orm.call('pos.order', 'action_send_to_folio', [[order.backendId || order.name]]);
                order.sent_to_folio = true;
                await this.popup.add(ConfirmPopup, {
                    title: 'Success',
                    body: 'Order sent to folio and added to room invoice.',
                });
                console.log('Order sent to folio, new order created');
                // Finalize: remove order, start new
                this.pos.removeOrder(order);
                this.pos.add_new_order();
            } catch (error) {
                console.error('Failed to send to folio:', error);
                await this.popup.add(ErrorPopup, {
                    title: 'Error',
                    body: 'Failed to send to folio. Check server logs.',
                });
            }
        }
    }
});