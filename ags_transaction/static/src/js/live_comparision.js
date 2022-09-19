odoo.define('ags_transaction.live_comparision', function (require) {
  'use strict';
  var FormRenderer = require('web.FormRenderer');
  var rpc = require('web.rpc');
  var core = require('web.core');
  var QWeb = core.qweb;
  var Widget = require('web.Widget');
  var ajax = require('web.ajax');

  var LiveComparision = Widget.extend({
    template: 'live_view_screen',
    init: function (parent, action) {
      this._super(parent);
      this.bill_queue_length = 0;
      this.view_shift_queue = false;
      this.trans_queue_length = 0;
      this.bills_by_name = {};
      this.trans_by_name = {};
      this.latest_bill_write_date = "";
      this.latest_trans_write_date = "";
      this.latest_saleorder_write_date = "";
      this.bill_tot = 0;
      this.tran_tot = 0;
      this.current_shift = "";
      this.manual_match = {};
      this.focus_trans = "";
      this.credit_or_card_trans = {};
      this.success = false;
      this.scheduler_state = true;
      this.users = {};
      this.customers = [];
      this.payment_type = [];
      this.irregular_trans = [];
      this.allow_manual_matching = false;
      this.request_shift_id = null;
      if (action.context.shift) {
        this.request_shift_id = action.context.shift;
        this.view_shift_queue = true;
      }

    },

    start: function () {
      var self = this;
      if (self.view_shift_queue) {
        console.log("Shift queue");
        ajax.jsonRpc('/ags/shift/queue', 'call', {
            'shift': self.request_shift_id
          })
          .then(function (data) {
            self.bill_tot = data['bill_tot']['bill_tot'];
            self.trans_tot = data['trans_tot']['trans_tot'];
            self.user_input_option(data['emp']);
            self.load_customers(data['customer']);
            self.load_payment_types(data['payment_type']);
            self.allow_manual_matching = data['allow_manual_matching'];
            self.data_render(data['bills'], data['trans'], data['bill_tot'], data['trans_tot'], 'Shift Queue', false);
          });

      } else {
        ajax.jsonRpc('/ags/live', 'call', {}).then(function (data) {
          self.bill_queue_length = data[0].length;
          self.push_bills(data[0]);
          self.push_trans(data[1]);
          self.write_latest_dates(data[4][0], data[5][0], data[11][0]);
          self.bill_tot = data[2]['bill_tot'];
          self.trans_tot = data[3]['trans_tot'];
          self.current_shift = data[6];
          self.user_input_option(data[8]);
          self.load_customers(data[9]);
          self.load_payment_types(data[10]);
          self.scheduler_state = data[7];
          self.allow_manual_matching = data[12];
          self.data_render(data[0], data[1], data[2], data[3], 'Live', true);
          self.highlight_irregular_trans()
        });
        self.refresh_data();
      }

    },
    highlight_irregular_trans: function () {
      var self = this;
      for (var i = 0; i < self.irregular_trans.length; i++) {
        var $irregular_trans = self.$el.find(".oe_tran_data[data-id='" + self.irregular_trans[i] + "']");
        $irregular_trans.addClass('irregular');
      }

    },
    send_mapped_data_to_server: function (view) {
      var self = this;
      var vals = {
        'manual_match': self.manual_match,
        'credit_or_card': self.credit_or_card_trans
      };
      self.manual_match = {};
      self.credit_or_card_trans = {};
      ajax.jsonRpc('/shift/queue/map', 'call', vals).then(function (data) {

      });

    },
    user_input_option: function (users) {
      var self = this;

      for (var i = 0; i < users.length; i++) {
        self.users[users[i]["id"]] = users[i]["name"];
      }
    },
    load_customers: function (customers) {
      var self = this;
      for (var i = 0; i < customers.length; i++) {
        self.customers[i] = customers[i];
      }
    },
    load_payment_types: function (types) {
      var self = this;
      for (var i = 0; i < types.length; i++) {
        self.payment_type[i] = types[i];
      }
    },
    set_option: function () {
      var self = this;
      var opt = '<option value="" disabled selected>Select the Customer</option>';
      for (var i = 0; i < self.customers.length; i++) {
        opt += '<option value=' + self.customers[i]["id"] + '>' + self.customers[i]["name"] + '</option>';
      }
      return opt;
    },
    set_payment_option: function () {
      var self = this;
      var opt = '<option value="" disabled selected>Select the Payment Type</option>';
      for (var i = 0; i < self.payment_type.length; i++) {
        opt += '<option value=' + self.payment_type[i]["id"] + '>' + self.payment_type[i]["name"] + '</option>';
      }
      return opt;
    },
    set_scheduler_state: function () {
      var self = this;
      self.$el.find('#togBtn').prop({
        checked: self.scheduler_state
      });

    },
    // Restrict Manual Matching 
    apply_access_rights: function () {
      var self = this;
      if (!self.allow_manual_matching) {
        self.$el.find('#manual_option').addClass('hide');
      }

    },

    events: {
      "click #togBtn": function () {
        var self = this;
        var state = $('#togBtn').prop('checked');
        ajax.jsonRpc('/ags/automap/stop', 'call', {
          'state': state
        }).then(function (error) {
          if (error) {
            Swal("Record cannot be modified right now", error, "warning");
            $('#togBtn').prop('checked', !state);
          }
        });


      },
      "click .compare": function () {
        var self = this;
        console.log("Compare shift:" + self.request_shift_id);
        ajax.jsonRpc('/ags/shift/compare', 'call', {
            'shift': self.request_shift_id
          })
          .then(function (data) {
            ajax.jsonRpc('/ags/shift/queue', 'call', {
                'shift': self.request_shift_id
              })
              .then(function (data) {
                console.log("Data:" + Object.entries(data));
                self.bill_tot = data['bill_tot']['bill_tot'];
                self.trans_tot = data['trans_tot']['trans_tot'];
                self.user_input_option(data['emp']);
                self.load_customers(data['customer']);
                self.load_payment_types(data['payment_type']);
                self.data_render(data['bills'], data['trans'], data['bill_tot'], data['trans_tot'], 'Shift Queue', false);
              });
          });
      },
      
      "click .remove_zero_value": function () {
        var self = this;
        console.log("Compare shift:" + self.request_shift_id);
        ajax.jsonRpc('/ags/remove_zero_value', 'call', {
            'shift': self.request_shift_id
          })
          .then(function (data) {
            ajax.jsonRpc('/ags/shift/queue', 'call', {
                'shift': self.request_shift_id
              })
              .then(function (data) {
                console.log("Data:" + Object.entries(data));
                self.bill_tot = data['bill_tot']['bill_tot'];
                self.trans_tot = data['trans_tot']['trans_tot'];
                self.user_input_option(data['emp']);
                self.load_customers(data['customer']);
                self.load_payment_types(data['payment_type']);
                self.data_render(data['bills'], data['trans'], data['bill_tot'], data['trans_tot'], 'Shift Queue', false);
              });
          });
      },
      
      "click .remove_all_match": function () {
        var self = this;
        console.log("Compare shift:" + self.request_shift_id);
        ajax.jsonRpc('/ags/remove_all_match_amount', 'call', {
            'shift': self.request_shift_id
          })
          .then(function (data) {
            ajax.jsonRpc('/ags/shift/queue', 'call', {
                'shift': self.request_shift_id
              })
              .then(function (data) {
                console.log("Data:" + Object.entries(data));
                self.bill_tot = data['bill_tot']['bill_tot'];
                self.trans_tot = data['trans_tot']['trans_tot'];
                self.user_input_option(data['emp']);
                self.load_customers(data['customer']);
                self.load_payment_types(data['payment_type']);
                self.data_render(data['bills'], data['trans'], data['bill_tot'], data['trans_tot'], 'Shift Queue', false);
              });
          });
      },
      
      "click #manual_option": function () {
        var self = this;
        self.$el.find('.oe_tran_data').focusin(function () {
          self.focus_trans = $(this).attr('data-id');

        });


      },

      "click .credit": function () {
        var self = this;
        var credit_state = $(".credit[data-id='" + self.focus_trans + "']").prop('checked');
        var opt = self.set_option();
        if (credit_state) {

          Swal({
            title: 'Credit Transaction Details',
            confirmButtonText: 'Confirm',
            showCancelButton: true,
            html: '<input id="swal-input1" class="swal2-input" placeholder="Bill Number">' +
              '<input id="swal-input2" class="swal2-input" placeholder="Comments">',
            preConfirm: function () {
              return new Promise(function (resolve) {
                if ($('#swal-input1').val()) {
                  resolve([
                    $('#swal-input1').val(),
                    $('#swal-input2').val(),
                  ])
                } else {
                  Swal.showValidationMessage('Fill all the details :(');
                  Swal.enableButtons();
                }
              })
            },


            allowOutsideClick: false,
            onOpen: function () {
              $('#swal-input1').focus()
            }
          }).then(function (result) {
            if (result.dismiss) {
              $(".credit[data-id='" + self.focus_trans + "']").prop('checked', !credit_state);
            }

            if (result.value[0]) {
              Swal("Done!", "", "success");
              var $target_trans = self.$el.find(".oe_tran_data[data-id='" + self.focus_trans + "']");
              var trans_amt = Number($target_trans.find('.amt').text());
              self.trans_tot -= trans_amt;
              $target_trans.addClass('dropped');
              $target_trans.css('display', 'block');
              $target_trans.css('-webkit-animation', 'fadeOut 10s');
              $target_trans.css('-webkit-animation-fill-mode', 'forwards');
              self.credit_or_card_trans[self.focus_trans] = {
                'tran': self.focus_trans,
                'cmt': result.value[1],
                'bill_no': result.value[0],
                'customer_id': '',
                'type': 'credit',
                'payment_id': '',
                'payment_tid': ''
              };
              self.update_trans_total();
              if (self.view_shift_queue) {
                self.send_mapped_data_to_server();
              }


            }
          }).catch(Swal.noop)


        }

      },
      "click .card": function () {
        var self = this;
        var opt = self.set_option();
        var payment_opt = self.set_payment_option();
        var card_state = $(".card[data-id='" + self.focus_trans + "']").prop('checked');
        if (card_state) {


          Swal({
            title: 'Card Transaction Details',
            confirmButtonText: 'Confirm',
            showCancelButton: true,
            html: '<input id="swal-input1" class="swal2-input" placeholder="Bill Number">' +
              '<select id="swal-select2" class="swal2-select">' + payment_opt + '</select>' +
              '<input id="swal-input3" class="swal2-input" placeholder="Transaction ID">' +
              '<input id="swal-input2" class="swal2-input" placeholder="Comments">',
            preConfirm: function () {
              return new Promise(function (resolve) {
                if ($('#swal-input1').val() && $('#swal-select2').val() && $('#swal-input3').val()) {

                  resolve([
                    $('#swal-input1').val(),
                    $('#swal-input2').val(),
                    $('#swal-select2').val(),
                    $('#swal-input3').val(),
                  ])
                } else {
                  Swal.showValidationMessage('Fill all the details :(');
                  Swal.enableButtons();
                }
              })
            },


            allowOutsideClick: false,
            onOpen: function () {
              $('#swal-input1').focus()
            }
          }).then(function (result) {
            if (result.dismiss) {
              $(".card[data-id='" + self.focus_trans + "']").prop('checked', !card_state);
            }

            if (result.value[0] && result.value[2] && result.value[3]) {
              Swal("Done!", "", "success");
              var $target_trans = self.$el.find(".oe_tran_data[data-id='" + self.focus_trans + "']");
              var trans_amt = Number($target_trans.find('.amt').text());
              self.trans_tot -= trans_amt;
              $target_trans.addClass('dropped');
              $target_trans.css('display', 'block');
              $target_trans.css('-webkit-animation', 'fadeOut 10s');
              $target_trans.css('-webkit-animation-fill-mode', 'forwards');
              self.credit_or_card_trans[self.focus_trans] = {
                'tran': self.focus_trans,
                'cmt': result.value[2],
                'bill_no': result.value[0],
                'customer_id': '',
                'type': 'card',
                'payment_id': result.value[2],
                'payment_tid': result.value[3]
              };
              self.update_trans_total();
              if (self.view_shift_queue) {
                self.send_mapped_data_to_server();
              }

            }
          }).catch(Swal.noop)


        }

      },
      "click .test": function () {
        var self = this;
        var test_state = $(".test[data-id='" + self.focus_trans + "']").prop('checked');
        if (test_state) {
          Swal({
            title: "Test Transaction",
            text: "Comments:",
            input: "text",
            showCancelButton: true,
          }).then(function (result) {

            if (result.dismiss) {
              $(".test[data-id='" + self.focus_trans + "']").prop('checked', !test_state);
            }
            if (result.value == '' || result.value) {
              Swal("Done!", "", "success");
              var $target_trans = self.$el.find(".oe_tran_data[data-id='" + self.focus_trans + "']");
              var trans_amt = Number($target_trans.find('.amt').text());
              self.trans_tot -= trans_amt;
              $target_trans.addClass('dropped');
              $target_trans.css('display', 'block');
              $target_trans.css('-webkit-animation', 'fadeOut 10s');
              $target_trans.css('-webkit-animation-fill-mode', 'forwards');
              self.credit_or_card_trans[self.focus_trans] = {
                'tran': self.focus_trans,
                'cmt': result.value,
                'type': 'test',
                'payment_id': '',
                'payment_tid': '',
                'bill_no': '',
                'customer_id': ''
              };
              self.update_trans_total();
              if (self.view_shift_queue) {
                self.send_mapped_data_to_server();
              }
            }

          });


        }

      },
      "click .other": function () {
        var self = this;
        var other_state = $(".other[data-id='" + self.focus_trans + "']").prop('checked');
        if (other_state) {
          Swal({
            title: "Others",
            text: "Comments:",
            input: "text",
            showCancelButton: true,
            inputValidator: function (value) {
              return !value && 'Write reason for matching :('

            }
          }).then(function (result) {

            if (result.dismiss) {
              $(".other[data-id='" + self.focus_trans + "']").prop('checked', !other_state);
            }
            if (result.value) {
              Swal("Done!", "", "success");
              var $target_trans = self.$el.find(".oe_tran_data[data-id='" + self.focus_trans + "']");
              var trans_amt = Number($target_trans.find('.amt').text());
              self.trans_tot -= trans_amt;
              $target_trans.addClass('dropped');
              $target_trans.css('display', 'block');
              $target_trans.css('-webkit-animation', 'fadeOut 10s');
              $target_trans.css('-webkit-animation-fill-mode', 'forwards');
              self.credit_or_card_trans[self.focus_trans] = {
                'tran': self.focus_trans,
                'cmt': result.value,
                'type': 'other',
                'payment_id': '',
                'payment_tid': '',
                'bill_no': '',
                'customer_id': ''
              };
              self.update_trans_total();
              if (self.view_shift_queue) {
                self.send_mapped_data_to_server();
              }
            }

          });


        }

      },
      "click #manual_match": function () {
        var self = this;
        var manual = new Array();
        var beh2 = "";
        var tran = "";

        self.$el.find('.oe_bill_data').draggable({
          cursor: 'move',
          snap: '.snap',
          revert: function (event, ui) {

            $(this).data("ui-draggable").originalPosition = {
              top: 0,
              left: 0
            };

            return !event;

          },
          drag: function (event, ui) {
            if ($(this).data('droppedin')) {
              $(this).data('droppedin').droppable('enable');
              $(this).data('droppedin', null);
              $(this).removeClass('dropped');
              tran = $(this).attr('data-dropped-Id');
              manual[tran] = {};

            }
          }
        });
        self.$el.find('.oe_tran_data').droppable({
          hoverClass: 'hovered',
          tolerance: 'pointer',
          drop: function (event, ui) {
            var drop_p = $(this).offset();
            var drag_p = ui.draggable.offset();
            var left_end = drop_p.left - drag_p.left;
            var top_end = drop_p.top - drag_p.top;
            ui.draggable.animate({
              top: '+=' + top_end,
              left: '+=' + left_end
            });
            ui.draggable.data('droppedin', $(this));

            $(this).droppable('disable');
          }
        });


        self.$el.find('.oe_tran_data').on("drop", function (event, ui) {
          tran = event.target.getAttribute('data-id');
          var transaction = $(this);
          manual[tran] = {'order_id':ui.draggable.attr('data-id'), 
                          'line_id':ui.draggable.attr('data-line-id')};
          ui.draggable.attr('data-dropped-Id', $(this).attr('data-id'));

          Swal({
            title: "Manual Matching!",
            text: "Reason for matching:",
            input: "text",
            confirmButtonText: 'Next →',
            showCancelButton: true,
            inputValidator: function (value) {
              return !value && 'Write reason for matching :('

            }
          }).then(function (result) {
            if (result.dismiss) {
              ui.draggable.animate({
                top: "0px",
                left: "0px"
              });
            }
            if (result.value) {
              Swal({
                title: "Manual Matching!",
                text: "Responsible person for mismatch:",
                input: 'select',
                confirmButtonText: 'Confirm',
                showCancelButton: true,
                inputOptions: self.users,
              }).then(function (result1) {
                if (result1.dismiss) {
                  ui.draggable.animate({
                    top: "0px",
                    left: "0px"
                  });
                }
                if (result1.value) {
                  self.manual_match[manual[tran], tran] = {
                    'bill': manual[tran]['order_id'],
                    'bill_line': manual[tran]['line_id'],
                    'tran': tran,
                    'cmt': result.value,
                    'responsible_person': result1.value
                  };
                  Swal("Done!", "", "success");
                  ui.draggable.addClass('dropped');
                  transaction.addClass('dropped');
                  self.bill_tot -= Number(ui.draggable.find('.amt').text());
                  self.trans_tot -= Number(transaction.find('.amt').text());
                  ui.draggable.css('display', 'block');
                  transaction.css('display', 'block');
                  transaction.css('-webkit-animation', 'fadeOut 5s');
                  ui.draggable.css('-webkit-animation', 'fadeOut 5s');
                  ui.draggable.css('-webkit-animation-fill-mode', 'forwards');
                  transaction.css('-webkit-animation-fill-mode', 'forwards');
                  self.update_bill_total();
                  self.update_trans_total();
                  if (self.view_shift_queue) {
                    self.send_mapped_data_to_server();
                  }
                }

              });
            }

          });


        });
      },

    },

    write_latest_dates: function (billdate, transdate, saleOrderdate) {
      var self = this;
      self.latest_bill_write_date = billdate['write_date'];
      self.latest_saleOrder_write_date = saleOrderdate['write_date'];
      self.latest_trans_write_date = transdate['write_date'];
    },
    push_bills: function (bills) {
      var self = this;
      for (var rec = 0; rec < bills.length; rec++) {
        //console.log("bills:" +self.bills_by_name);
        self.bills_by_name[bills[rec].no] = bills[rec];
      }
    },
    push_trans: function (trans) {
      var self = this;
      for (var rec = 0; rec < trans.length; rec++) {
        self.trans_by_name[trans[rec].tid] = trans[rec];
        if (trans[rec]['irregular_trans']) {
          self.irregular_trans.push(trans[rec].tid);
        }

      }
    },
    update_bill_total: function () {
      var self = this;
      var billtot = self.bill_tot;
      console.log("bill tot:" + self.bill_tot);
      self.$el.find('.bill_tot').text(parseFloat(billtot).toFixed(2));
    },
    update_trans_total: function () {
      var self = this;
      var transtot = self.trans_tot;
      self.$el.find('.trans_tot').text(parseFloat(transtot).toFixed(2));
    },


    render_bill_data: function (bills) {
      var self = this;
      console.log("Render bill:"+self.allow_manual_matching);
      for (var i = 0; i < bills.length; i++) {
        var bill_exist = self.bills_by_name[bills[i]['no']];
        if (!bill_exist) {
          self.bill_tot += bills[i]['amt'];
          var bill = QWeb.render("bill_details", {
            widget: self,
            allow: self.allow_manual_matching,
            bill: bills[i]
          });
          $(bill).prependTo(self.$el.find('.bill_details_container')).show();

        }
      }
    },

    render_trans_data: function (trans) {
      var self = this;
      console.log("Render Trans:"+self.allow_manual_matching);
      for (var i = 0; i < trans.length; i++) {
        var trans_exist = self.trans_by_name[trans[i]['tid']];
        if (!trans_exist) {
          self.trans_tot += trans[i]['amt'];
          var tran = QWeb.render("trans_details", {
            widget: self,
            allow: self.allow_manual_matching,
            tran: trans[i]
          });
          $(tran).prependTo(self.$el.find('.tran_details_container')).show();
          if (trans[i]['irregular_trans']) {
            var $irregular_trans = self.$el.find(".oe_tran_data[data-id='" + trans[i]['tid'] + "']");
            console.log("Changing irregular color");
            $irregular_trans.addClass('irregular');
          }

        }

      }
    },
    generate_random_color: function () {
      var colors = ['#afeeee', '#98fb98', '#eee8aa', '#ffe4b5', '#ffe4e1', '#f5fffa', '#fafad2', '#e0ffff', '#b0e0e6', '#ffdab9', '#ffb6c1', '#fffacd'];
      var random_color = colors[Math.floor(Math.random() * colors.length)];
      return random_color;
    },


    remove_matched: function (matched) {
      var self = this;
      for (var i = 0; i < matched.length; i++) {
        var current_bill = matched[i]['bill_no']+matched[i]['bill_line'];

        if (matched[i]['bill_no']) {
          self.bill_tot -= matched[i]['bill_amt'];
        }
        self.trans_tot -= matched[i]['trans_amt'];
        var $target_bill = self.$el.find(".oe_bill_data[data-match-ref='" + current_bill + "']");
        var color = self.generate_random_color();
        $target_bill.addClass('highlight');
        ($target_bill).css('background', color);
        var current_trans = matched[i]['tran_no'];
        var $target_trans = self.$el.find(".oe_tran_data[data-id='" + current_trans + "']");
        $target_trans.addClass('highlight');
        ($target_trans).css('background', color);
        ($target_bill).css('-webkit-animation', 'fadeOut 6s');
        ($target_bill).css('animation', 'fadeOut 6s');
        ($target_bill).css('display', 'block');
        //($target_bill).css('height', '0');
        ($target_bill).css('-webkit-animation-fill-mode', 'forwards');
        ($target_bill).css('animation-fill-mode', 'forwards');


        ($target_trans).css('-webkit-animation', 'fadeOut 5s');
        ($target_trans).css('-webkit-animation-fill-mode', 'forwards');
        ($target_trans).css('animation', 'fadeOut 5s');
        ($target_trans).css('animation-fill-mode', 'forwards');
        ($target_trans).css('display', 'block');
        //($target_trans).css('height', '0');

      }
    },
    remove_highlight: function () {
      var self = this;
      self.$el.find('.highlight').each(function () {
        $(this).remove();
      });
    },
    render: function (bill, trans, bill_tot, trans_tot, matched) {
      var self = this;
      self.render_bill_data(bill);
      self.update_bill_total();
      self.update_trans_total();
      self.render_trans_data(trans);
      self.push_bills(bill);
      self.push_trans(trans);
      if (matched) {
        self.remove_matched(matched);
      }
    },

    refresh_data: function (view) {
      var self = this;
      setInterval(function () {
        if (self.latest_bill_write_date && self.latest_trans_write_date && self.latest_saleOrder_write_date) {
          var vals = {
            'bill_date': self.latest_bill_write_date,
            'trans_date': self.latest_trans_write_date,
            'saleOrder_date': self.latest_saleOrder_write_date,
            'manual_match': self.manual_match,
            'credit_or_card': self.credit_or_card_trans
          };
          self.manual_match = {};
          self.credit_or_card_trans = {};
          ajax.jsonRpc('/ags/live/data_refresh', 'call', vals).then(function (data) {
            if (data[7] != self.current_shift) {
              location.reload();
            }
            self.write_latest_dates(data[5][0], data[6][0], data[8][0]);
            self.render(data[0], data[1], data[2], data[3], data[4]);
          });
        }
      }, 5000);

    },
    remove_matched_bill: function (bill) {
      var self = this;
      for (var i = 0; i < bill.length; i++) {
        var current = bill[i]['no'];
        var $target = self.$el.find(".oe_bill_data[data-id='" + current + "']");
        $target.hide('slow', function () {
          $target.remove();
        });
        $target.addClass('highlight');
      }
    },
    remove_matched_transaction: function (tran) {
      var self = this;
      for (var i = 0; i < tran.length; i++) {
        var current = tran[i]['tid'];
        var $target = self.$el.find(".oe_tran_data[data-id='" + current + "']");
        $target.addClass('highlight');
        $target.hide('slow', function () {
          $target.remove();
        });
      }
    },


    data_render: function (bills, trans, bill_tot, trans_tot, title, toggle) {
      var self = this;
      console.log("Data render:" +self.allow_manual_matching);
      self.$el.html(QWeb.render("live_view_screen", {
        widget: self,
        title: title,
        bills: bills,
        trans: trans,
        bill_tot: bill_tot,
        trans_tot: trans_tot,
        allow: self.allow_manual_matching,
        toggle: toggle
      }));
      self.set_scheduler_state();
      //self.apply_access_rights();

    },


  });

  core.action_registry.add('live_view', LiveComparision);

});
