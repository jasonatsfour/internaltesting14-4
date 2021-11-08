odoo.define('kanban_scan.reordering_kanban', function (require) {
"use strict";

var core = require('web.core');
var Widget = require('web.Widget');
var Dialog = require('web.Dialog');
var _t = core._t;
var AbstractAction = require('web.AbstractAction');
var MrpReorderingKanban = AbstractAction.extend({
    template: 'MrpReorderingKanban',

    events: {
        "click .o_barcode_kfm_krr_scan": function () { this.scan_barcode() },
        "click #confirm_button": function() { this.confirm_krr() },
        "click #confirm_button_kfm":function() { this.confirm_kfm() },
        "click #open_receipt_data": function() {this.open_receipt_data() },
        "click #open_internal_transfer" : function() { this.open_internal_transfer() },
        "click #open_manufacturing_data": function() { this.open_manufacturing_data() },
        "click #open_delivery_order": function() { this.open_delivery_order() },
        "click #open_purchase_order_success": function() { this.open_purchase_order_success() },
        "click #picking_button": function() { this.picking_button() },
        'click [action]': 'open_list_record',
        "click #cancel_scan": function() { this.cancel_scan() },
        "click #open_stock_receipt_data": function() { this.open_stock_receipt_data() },
        "click #confirm_receipt":function() { this.confirm_receipt() },

    },

    init: function(parent, action) {
        var self = this;
        this._super.apply(this, arguments);
        this.next_action = 'purchase.purchase_rfq';
        this.context = action.context
    },

    start: function() {
        var self = this;
        this._super;
        if (this.$el != null){
            this.$el.find('.o_barcode_kfm_krr_scan').focus()
            this.$el.find("#barcode_unmatched").hide()
            this.$el.find("#barcode_matched").hide()
            this.$el.find("#barcode_matched_krr").hide()
            this.$el.find("#barcode_receipt").hide()
            this.$el.find("#rfq_created").hide()
            this.$el.find("#receipt_val").hide();
            this.$el.find("#rfq_updated").hide()
            this.$el.find("#not_internal_transfer").hide()
            this.$el.find("#location_error").hide()
            this.$el.find("#mrp_created").hide()
            this.$el.find('#schedule_date').hide();
            this.$el.find("#delivery_state").hide();
        }
    },

    scan_barcode: function(){
        var self = this;
        var barcode_data = $('#barcode').val();
        this._rpc({
            model: 'mrp.kanban.reordering',
            method: 'match_barcode_generic',
            args: [barcode_data, barcode_data, barcode_data],
            context: self.context
        }).then(function (match_data){
            $('#barcode').on('input', function(){
                    $("#barcode_unmatched").hide();
                });
            // Raise warning if Data not matched.
            if (match_data == false){
                $("#barcode_unmatched").show();
                $("#barcode_matched_krr").hide();
                $("#barcode_matched").hide();
                $("#barcode_receipt").hide();
                $("#rfq_created").hide();
                $("#rfq_updated").hide();
                $("#mrp_created").hide();
                $("#receipt_val").hide();
                $('#schedule_date').hide();
                $("#delivery_state").hide();
                $("#not_internal_transfer").hide();
                $("#location_error").hide();
                $('.o_barcode_kfm_krr_scan').show();
                $('.o_kfm_krr_kiosk_mode').show();
                $(".barcode_field").val('').focus();
            }else if (match_data.kfm.create_picking == true){
                $("#rfq_created").show();
                $(".barcode_field").val('').focus();
            }else if (match_data.kfm.error == 'location_error'){
                $("#location_error").show();
                $(".barcode_field").val('').focus();
            }
            else{
                if (match_data.krr){
                    // Show output if Kanban Reordering Data matched.
                    $('.o_barcode_kfm_krr_scan').hide();
                    $('.o_kfm_krr_kiosk_mode').hide();
                    $("#barcode_unmatched").hide();
                    $("#barcode_matched").hide();
                    $("#barcode_receipt").hide();
                    $("#receipt_val").hide();
                    $("#rfq_created").hide();
                    $("#rfq_updated").hide();
                    $("#mrp_created").hide();
                    $('#schedule_date').hide();
                    $("#delivery_state").hide();
                    $("#not_internal_transfer").hide();
                    $("#krr_name").text(match_data.krr.name);
                    $("#krr_product").text(match_data.krr.product);
                    $("#krr_vendor").text(match_data.krr.vendor);
                    $("#krr_quantity").text(match_data.krr.quantity);
                    // Purchase
                    self.kkr_id = match_data.krr.kkr_id,
                    self.purchase_exist = match_data.krr.purchase_exist
                    self.purchase_id = match_data.krr.purchase_id,
                    self.product_id =  match_data.krr.product
                    self.quantity = match_data.krr.quantity
                    self.vendor_id  = match_data.krr.vendor
                    self.purchase_number = match_data.krr.current_purchase_order_rec_name
                    var table_html = {};
                    // Purchase table
                    $('#purchase_table tr').not(':first').remove();
                    _.each(match_data.krr.purchase_list, function (purchase_data) {
                        self.purchase_ids = purchase_data.purchase_id
                        table_html += '<tr><td>' + purchase_data.purchase_type +
                         '</td><td><a action="open_list_record" href="#" data-id='+ self.purchase_ids + '>' + purchase_data.purchase_number +
                         '</a></td><td>' + purchase_data.purchase_vendor +
                         '</td><td>' + purchase_data.purchase_qty +
                         '</td><td>' + purchase_data.received_qty +
                         '</td><td>' + purchase_data.purchase_scheduled_date + '</td></tr>';
                    });
                    $('#purchase_table tr').first().after(table_html);

                    $("#barcode_matched_krr").show();
                }
                // Receipt scanning
                if (match_data.receipt){
                    $("#barcode_receipt").show()
                    $('.o_barcode_kfm_krr_scan').hide();
                    $('.o_kfm_krr_kiosk_mode').hide();
                    $("#barcode_unmatched").hide();
                    $("#barcode_matched_krr").hide();
                    $("#mrp_created").hide();
                    $("#receipt_val").hide();
                    $('#schedule_date').hide();
                    $("#delivery_state").hide();
                    $("#not_internal_transfer").hide();
                    $("#receipt_source").text(match_data.receipt.source);
                    self.receipt_record_id = match_data.receipt.receipt_record_id;
                    // Receipt table
                    if (match_data.receipt.receipt_list){
                        $("#receip_details").removeClass('d-none');
                        $('#receipt_table tr').not(':first').remove();
                        _.each(match_data.receipt.receipt_list, function (receipt_data) {
                            self.receipt = receipt_data.receipt_id
                            table_html += '<tr><td><a action="open_list_record" href="#" data-id='+ self.receipt + '>' + receipt_data.name +
                             '</a></td><td>' + receipt_data.source_location +
                             '</td><td>'+ receipt_data.destination_location +
                             '</td><td>'+ receipt_data.schedule_date +
                             '</td><td>'+ receipt_data.state +'</td></tr>';
                        });
                    }else{
                        $("#receip_details").addClass('d-none');
                    }
                    $('#receipt_table tr').first().after(table_html);
                }
                if (match_data.kfm){
                    // Show Output if Manufacturing Data Mtached.
                    $('.o_barcode_kfm_krr_scan').hide();
                    $('.o_kfm_krr_kiosk_mode').hide();
                    $("#barcode_unmatched").hide();
                    $("#barcode_matched_krr").hide();
                    $('#schedule_date').hide();
                    $("#delivery_state").hide();
                    $("#barcode_receipt").hide();
                    $("#receipt_val").hide();
                    $("#mrp_created").hide();
                    $("#not_internal_transfer").hide();
                    $("#kfm_name").text(match_data.kfm.name);
                    $("#kfm_type").text(match_data.kfm.type);
                    $("#kfm_source_loc").text(match_data.kfm.source_location);
                    $("#kfm_destination_loc").text(match_data.kfm.destination_location);
                    self.current_stock_id = match_data.kfm.current_stock_picking_rec_id;
                    self.delivery_stock_id = match_data.kfm.stock_picking_delivery_id;
                    self.receipt_stock_id = match_data.kfm.stock_picking_receipt_id;
                    $("#kfm_schedule_date").text(match_data.kfm.schedule_date);
                    $("#kfm_product").text(match_data.kfm.product);
                    self.current_mrp_id = match_data.kfm.current_mrp_production_rec_id;
                    self.kfm_id = match_data.kfm.kfm_id,
                    self.product_id =  match_data.kfm.product
                    self.quantity = match_data.kfm.quantity
                    var table_html = {};
                    if (match_data.kfm.mrp_list){
                        // Manufacturing, Internal Transfer, Inter-warehouse table
                        $("#mrp_details").removeClass('d-none');
                        $('#mrp_table tr').not(':first').remove();
                        _.each(match_data.kfm.mrp_list, function (mrp_data) {
                            if (mrp_data.manuf_id){
                                $('#schedule_date').hide();
                                $("#delivery_state").hide();
                                self.manuf_id = mrp_data.manuf_id
                                table_html += '<tr><td><a href="#" action="open_list_record" data-id='+ self.manuf_id +'>'+ mrp_data.mrp_number +
                                 '</a></td><td>' + mrp_data.source_location +
                                 '</td><td>' + mrp_data.destination_location +
                                 '</td><td>' + mrp_data.qty + '</td></tr>';
                            }else if(mrp_data.internal_transfer_id){
                                $('#schedule_date').hide();
                                $("#delivery_state").hide();
                                self.internal_transfer_id = mrp_data.internal_transfer_id
                                table_html += '<tr><td><a href="#" action="open_list_record" data-id='+ self.internal_transfer_id +'>'+ mrp_data.mrp_number +
                                 '</a></td><td>' + mrp_data.source_location +
                                 '</td><td>' + mrp_data.destination_location +
                                 '</td><td>' + mrp_data.qty + '</td></tr>';
                            }else if (mrp_data.delivery_transfer_id){
                                $('#schedule_date').show()
                                $("#delivery_state").show()
                                self.delivery_transfer_id = mrp_data.delivery_transfer_id
                                table_html += '<tr><td><a href="#" action="open_list_record" data-id='+ self.delivery_transfer_id +'>'+ mrp_data.mrp_number +
                                 '</a></td><td>' + mrp_data.source_location +
                                 '</td><td>' + mrp_data.destination_location +
                                 '</td><td>' + mrp_data.qty +
                                 '</td><td>' + mrp_data.delivery_scheduled_date +
                                 '</td><td>' + mrp_data.delivery_status + '</td></tr>';
                            }
                            // else if(mrp_data.receipt_transfer_id){
                            //     self.receipt_transfer_id = mrp_data.receipt_transfer_id
                            //     table_html += '<tr><td><a href="#" action="open_list_record" data-id='+ self.receipt_transfer_id +'>'+ mrp_data.mrp_number +
                            //      '</a></td><td>' + mrp_data.source_location +
                            //      '</td><td>' + mrp_data.destination_location +
                            //      '</td><td>' + mrp_data.receipt_scheduled_date +
                            //      '</td><td>' + mrp_data.qty + '</td></tr>';
                            // }
                        });
                    }else{
                        $("#mrp_details").addClass('d-none');
                    }
                    $('#mrp_table tr').first().after(table_html);
                    $("#barcode_matched").show();
                }
            }
        });
    },

    confirm_krr: function(){
        var self = this;
        if (this.purchase_exist == true){
            this._rpc({
                model: 'kanban.reordering',
                method: 'update_po',
                args: [self.purchase_id, self.kkr_id],
                context: self.context
            }).then(function (match_data) {
                $('#barcode').on('input', function(){
                    $("#rfq_updated").hide();
                });
                $("#purchaseid").text(self.purchase_number)
                $("#barcode_matched_krr").hide();
                $("#receipt_val").hide();
                $("#mrp_created").hide();
                $("#rfq_updated").show();
                $('#schedule_date').hide();
                $("#delivery_state").hide();
                $('.o_barcode_kfm_krr_scan').show();
                $('.o_kfm_krr_kiosk_mode').show();
                $(".barcode_field").val('').focus();
            });
        }else{
            this._rpc({
                model: 'kanban.reordering',
                method: 'create_po',
                args: [self.kkr_id],
                context: self.context
            }).then(function (match_data) {
                $('#barcode').on('input', function(){
                    $("#rfq_created").hide();
                });
                $("#purchase_id").val(match_data[0])
                $("#barcode_matched_krr").hide();
                $("#mrp_created").hide();
                $("#receipt_val").hide();
                $("#rfq_created").show();
                $('#schedule_date').hide();
                $("#delivery_state").hide();
                $('.o_barcode_kfm_krr_scan').show();
                $('.o_kfm_krr_kiosk_mode').show();
                $(".barcode_field").val('').focus();
            });
        }
    },

    confirm_kfm : function(){
        var self = this;
        this._rpc({
                model: 'mrp.kanban.reordering',
                method: 'confirm_kfm_data',
                args: [this.kfm_id],
                context: self.context
            }).then(function (match_data) {
                if (match_data){
                    $('#barcode').on('input', function(){
                        $("#mrp_created").hide();
                        $("#not_internal_transfer").hide();
                    });
                    if (match_data.internal_transfer == false){
                        $("#not_internal_transfer").show();
                        $("#mrp_created").hide();
                        $("#receipt_val").hide();
                        $('#schedule_date').hide();
                        $("#delivery_state").hide();
                        $("#mrp_order").addClass('d-none');
                        $("#receipt").addClass('d-none');
                        $("#delivery").addClass('d-none');
                        $("#internal").addClass('d-none');
                        $("#barcode_matched").hide();
                        $('.o_barcode_kfm_krr_scan').show();
                        $('.o_kfm_krr_kiosk_mode').show();
                        $(".barcode_field").val('').focus();
                    }else if (match_data.internal_transfer == true){
                        $("#internal_transfer_id").val(match_data.internal_picking_id)
                        $("#internal").removeClass('d-none');
                        $('#schedule_date').hide();
                        $("#delivery_state").hide();
                        $("#mrp_order").addClass('d-none');
                        $("#receipt").addClass('d-none');
                        $("#delivery").addClass('d-none');
                        $("#mrp_created").show();
                        $("#receipt_val").hide();
                        $("#barcode_matched").hide();
                        $('.o_barcode_kfm_krr_scan').show();
                        $('.o_kfm_krr_kiosk_mode').show();
                        $(".barcode_field").val('').focus();
                    }else if(match_data.manufacturing_order == true){
                        $("#manuf_order_id").val(match_data.manufacturing_order_id)
                        $("#mrp_order").removeClass('d-none');
                        $("#internal").addClass('d-none');
                        $("#receipt").addClass('d-none');
                        $("#delivery").addClass('d-none');
                        $("#mrp_created").show();
                        $("#receipt_val").hide();
                        $('#schedule_date').hide();
                        $("#delivery_state").hide();
                        $("#barcode_matched").hide();
                        $('.o_barcode_kfm_krr_scan').show();
                        $('.o_kfm_krr_kiosk_mode').show();
                        $(".barcode_field").val('').focus();
                    }else if (match_data.inter_warehouse == true){
                        $("#delivery_order_id").val(match_data.delivery_order_id)
                        $("#receipt_id").val(match_data.receipt_id)
                        $("#receipt").removeClass('d-none');
                        $("#delivery").removeClass('d-none');
                        $("#mrp_order").addClass('d-none');
                        $("#internal").addClass('d-none');
                        $("#mrp_created").show();
                        $("#receipt_val").hide();
                        $('#schedule_date').hide();
                        $("#delivery_state").hide();
                        $("#barcode_matched").hide();
                        $('.o_barcode_kfm_krr_scan').show();
                        $('.o_kfm_krr_kiosk_mode').show();
                        $(".barcode_field").val('').focus();
                    }else if(match_data.physical == true){
                        $("#receipt").addClass('d-none');
                        $("#delivery").addClass('d-none');
                        $("#internal").addClass('d-none');
                        $("#mrp_order").addClass('d-none');
                        $("#barcode_matched").hide();
                        $('#schedule_date').hide();
                        $("#delivery_state").hide();
                        $('.o_barcode_kfm_krr_scan').show();
                        $('.o_kfm_krr_kiosk_mode').show();
                        $(".barcode_field").val('').focus();
                    }
                }
            })
    },

    confirm_receipt: function(){
        var self = this;
        var text = _t("Do you really want to confirm Receipt?");
        Dialog.confirm(this, text, {
            confirm_callback: function () {
                self._rpc({
                        model: 'stock.picking',
                        method: 'confirm_receipt_data',
                        args: [self.receipt_record_id],
                    })
                    .then(function (match_data) {
                        if (match_data){
                            $('#barcode').on('input', function(){
                                $("#receipt_val").hide();
                            });
                            if (match_data.receipt_value == false){
                                $("#receipt_val").show();
                                $('#schedule_date').hide();
                                $("#delivery_state").hide();
                                $("#receipt_not_validate").removeClass('d-none');
                                $("#receipt_validate").addClass('d-none');
                                $("#barcode_receipt").hide()
                                $("#barcode_unmatched").hide();
                                $("#barcode_matched").hide();
                                $("#barcode_matched_krr").hide();
                                $("#rfq_created").hide();
                                $("#rfq_updated").hide();
                                $('.o_barcode_kfm_krr_scan').show();
                                $('.o_kfm_krr_kiosk_mode').show();
                                $(".barcode_field").val('').focus();
                            }else{
                                $("#stock_receipt").val(self.receipt_record_id)
                                $("#receipt_val").show();
                                $('#schedule_date').hide();
                                $("#delivery_state").hide();
                                $("#receipt_validate").removeClass('d-none');
                                $("#receipt_not_validate").addClass('d-none')
                                $("#barcode_receipt").hide()
                                $("#barcode_unmatched").hide();
                                $("#barcode_matched").hide();
                                $("#barcode_matched_krr").hide();
                                $("#rfq_created").hide();
                                $("#rfq_updated").hide();
                                $('.o_barcode_kfm_krr_scan').show();
                                $('.o_kfm_krr_kiosk_mode').show();
                                $(".barcode_field").val('').focus();
                            }
                        }
                    });
                }
            });
    },

    open_receipt_data :function(){
        var self = this;
        var receipt = $("#receipt_id").val()
        if(receipt){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(receipt),
                target: 'current'
            });
        }
    },

    open_stock_receipt_data :function(){
        var self = this;
        if(self.receipt_record_id){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: self.receipt_record_id,
                target: 'current'
            });
        }
    },

    open_internal_transfer : function(){
        var self = this;
        var internal_transfer = $("#internal_transfer_id").val()
         if (internal_transfer){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(internal_transfer),
                target: 'current'
            });
        }
    },

    open_manufacturing_data :function(){
        var self = this;
        var mrp_num = $("#manuf_order_id").val()
        if (mrp_num){
           self.do_action({
                name: 'MRP Production',
                res_model: 'mrp.production',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(mrp_num),
                target: 'current'
            });
        }
    },

    open_delivery_order : function(){
        var self = this;
        var delivery_order = $("#delivery_order_id").val()
        if (delivery_order){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(delivery_order),
                target: 'current'
            });
        }
    },

    open_purchase_order_success : function(){
        var self = this;
        if (self.purchase_id){
            self.do_action({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: self.purchase_id,
                target: 'current'
            });
        }
        else{
            var purchase_num = $("#purchase_id").val()

            self.do_action({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: parseInt(purchase_num),
                target: 'current'
            });
        }
    },

    picking_button: function(){
        var self = this;
        this._rpc({
                model: 'mrp.kanban.reordering',
                method: 'open_picking',
                args: [],
                context: self.context
            })
    },

    open_list_record: function(e){
        var self = this;
        var record = $(e.target).data();
        if (self.purchase_id || self.purchase_ids){
            self.do_action({
                name: 'Requests for Quotation',
                res_model: 'purchase.order',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: record.id,
                target: 'current'
            });
        }
        else if (self.current_mrp_id){
            self.do_action({
                name: 'MRP Production',
                res_model: 'mrp.production',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: record.id,
                target: 'current'
            });
        }else if(self.current_stock_id){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: record.id,
                target: 'current'
            });
        }else if(self.receipt_stock_id){
            self.do_action({
                name: 'Stock Operations',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: record.id,
                target: 'current'
            });
        }else if(self.receipt_record_id){
            self.do_action({
                name: 'Stock Receipt',
                res_model: 'stock.picking',
                views: [[false, 'form']],
                type: 'ir.actions.act_window',
                view_type: 'form',
                view_mode: 'form',
                res_id: record.id,
                target: 'current'
            });
        }
    },

    cancel_scan: function(){
        var self = this;
        $("#barcode_unmatched").hide();
        $("#barcode_matched").hide();
        $("#barcode_matched_krr").hide();
        $("#rfq_created").hide();
        $("#rfq_updated").hide();
        $('#schedule_date').hide();
        $("#delivery_state").hide();
        $("#barcode_receipt").hide();
        $('.o_barcode_kfm_krr_scan').show();
        $('.o_kfm_krr_kiosk_mode').show();
        $(".barcode_field").val('').focus();
    },

});

core.action_registry.add('mrp_reordering_kanban', MrpReorderingKanban);

return MrpReorderingKanban;

});
