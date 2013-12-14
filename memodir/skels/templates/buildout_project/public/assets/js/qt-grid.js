/**
 * Created by ericqu on 11/26/13.
 */

(function (root, $, _, Backbone, Backgrid) {
    var QTGrid = root.QTGrid = {

    };

    QTGrid.RESTUrl = function (url) {

    };

    QTGrid.Model = Backbone.Model.extend({});

    QTGrid.Collection = function (url) {
        var Models = Backbone.PageableCollection.extend({
            model: QTGrid.Model,
            url: url,
            state: {
                pageSize: 20,
                firstPage: 0
            },
            queryParams: {
                pageSize: "limit",
                currentPage: null,
                sortKey: "order_by",
                offset: function () { return this.state.currentPage * this.state.pageSize; }
            },
            parseRecords: function(resp) {
                return resp.objects;
            },
            parseState: function (resp, queryParams, state, options) {
              return {totalRecords: resp.meta.total_count};
            },
            setSorting: function (sortKey, order, options) {
                if (sortKey) {
                    if (order === -1) sortKey = "-" + sortKey;
                }
                return Backbone.PageableCollection.prototype.setSorting.call(this, sortKey, order, options);
            }
        });
        return new Models()
    };

    QTGrid.ATRRTCSColorfulRow = Backgrid.Row.extend({

        attributes: function() {
            var status_color = {
                'OK': 'green',
                'NOK': 'red',
                'NT': 'black',
                'NI': '#ff9900',
                'NT_D': "#00619e"
            };

            var status = this.model.get('status');

            if (status in status_color){
                return {
                    style: "color:" + status_color[status]
                }
            }

            return {}

        }

    });

    QTGrid.QtUriCell = Backgrid.QtUriCell = Backgrid.UriCell.extend({

       render: function () {
           this.$el.empty();
           var formattedValue;
           var uri;
           var fk_field = "fk_field" in this.column.attributes ? this.column.get("fk_field") : "";
           if (fk_field) {
                var fk_model = this.model.get(this.column.get("name"));
                formattedValue = this.formatter.fromRaw(fk_model[fk_field]);
                uri = "absolute_url" in fk_model ? fk_model["absolute_url"] : "";
           } else {
                formattedValue = this.formatter.fromRaw(this.model.get(this.column.get("name")));
                uri = this.model.get("absolute_url");
           }

           this.$el.append($("<a>", {
              tabIndex: -1,
              href: uri,
              title: formattedValue
           }).text(formattedValue, uri));
           this.delegateEvents();
           return this;
      }
    });

    QTGrid.QtOprationCell = Backgrid.QtOprationCell = Backgrid.UriCell.extend({

        render: function() {
            this.$el.empty();

            var op = this.column.get("name");

            var formattedValue = op;

            var i_node = "";

            if (formattedValue == "edit") {
                op = "update";
                i_node = '<i class="fa fa-file-text-o fa-lg"></i>';
            } else {
                i_node = '<i class="fa fa-trash-o fa-lg"></i>';
            }
            var uri = this.model.get("absolute_url") + op;
            var a_node = $("<a>", {
              tabIndex: -1,
              href: uri,
              title: formattedValue
            });
            a_node[0].innerHTML = i_node;

            this.$el.append(a_node);
            this.delegateEvents();
            return this;
        },

        attributes: function() {
           return {style : "width:25px;border-right: 0"}
        }

    });

    QTGrid.Columns = function (cols) {

        return [
            {

                // name is a required parameter, but you don't really want one on a select all column
                name: "",

                // Backgrid.Extension.SelectRowCell lets you select individual rows
                cell: "select-row",

                // Backgrid.Extension.SelectAllHeaderCell lets you select all the row on a page
                headerCell: "select-all",

                renderable: false

            }
        ].concat(cols);
    };

    QTGrid.SelectFilter = Backgrid.Extension.ServerSideFilter.extend({
            // filters
            filter: null,

            events: {
              "change": "search",
              "submit": function (e) {
                e.preventDefault();
                this.search();
              }
            },

            template: _.template('<p><label><%- filter.title %></label><span class="field"></span><select class="selectpicker1" name="<%- filter.name %>" id="<%- filter.id %>"></select>'),

            initialize: function (options) {
                Backgrid.requireOptions(options, ["filter"]);
                Backgrid.Extension.ServerSideFilter.prototype.initialize.apply(this, arguments);

                this.filter = options.filter;
                this.name = this.filter.name;

                var collection = this.collection, self = this;
//                if (Backbone.PageableCollection &&
//                      collection instanceof Backbone.PageableCollection &&
//                      collection.mode == "server") {
//                    collection.queryParams[this.name] = function () {
//                      return self.$el.find(":selected").val();
//                    };
//                }

                this.listenTo(collection, "resetQueryParam", this.resetQueryParam);

            },

            search: function (e) {
                if (e) e.preventDefault();
                var data = {};
                data[this.name] = this.$el.find(":selected").val();

                if (this.filter.hasNext) {
                    this.collection.trigger("resetQueryParam", data, this.filter.level);
                }

                for (var key in data) {
                    this.collection.queryParams[key] = data[key];
                }

                this.collection.fetch({data: data, reset: true});
            },

            resetQueryParam: function (data, level) {
                if (this.filter.level <= level) return;

                data[this.name] = '0';
            },

            render: function () {
              this.$el.empty().append(this.template({
                filter: this.filter
              }));
              this.delegateEvents();
              return this;
            }
        }
    );


    QTGrid.RenderTo = function (data_container, filter_container, url, cols, filters, row) {

        var collection = QTGrid.Collection(url);

        $(document).ready(function () {

            // Initialize a new Grid instance
            var grid;
            var r = row ? row : Backgrid.Row;
            grid = new Backgrid.Grid({
                row: r,
                columns: QTGrid.Columns(cols),
                collection: collection
            });

            // Initialize the paginator
            var paginator = new Backgrid.Extension.Paginator({
              collection: collection
            });

            if (filters) {
                _.each(filters, function( filter ){
                    var sf = new QTGrid.SelectFilter({
                        collection: collection,
                        filter: filter
                    });
                    filter_container.append(sf.render().$el)
                })
            }

            // Initialize filer to search fields contains the given value
            var filter = new Backgrid.Extension.ServerSideFilter({
              collection: collection,
              placeholder: "Input regex to search"
            });
            // Add some space to the filter and move it to the right
            filter.$el.css({float: "right", margin: "20px"});

            // Render the grid and attach the root to your HTML document
            data_container.append(grid.render().$el);
            data_container.append(paginator.render().$el);
            data_container.prepend(filter.render().$el);

            // Fetch some countries from the url
            collection.fetch({reset: true});
        });

    }


}(this, jQuery, _, Backbone, Backgrid));
