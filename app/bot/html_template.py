from app.env_variables import CURRENCY

chart_template = """
        <html>
          <head>
          <meta charset="utf-8">
            <title>Month expenses</title>
            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            <script type="text/javascript">
              google.charts.load('current', {'packages':['corechart']});
              google.setOnLoadCallback(drawTable);
              function drawTable() {
                var json_data = new google.visualization.arrayToDataTable(%(json)s);
                var formatter = new google.visualization.NumberFormat({prefix: '""" + CURRENCY + """ '});
                formatter.format(json_data, 1)
                var options = {
                    title: 'Month Expenses',
                    is3D: true,
                    pieSliceText: 'label',
                    chartArea: {'width': '100%%', 'height': '80%%'},
                    sliceVisibilityThreshold: 0,
                    legend: {
                        labeledValueText: 'both',
                        position: 'labeled'
                    }
                };
                var chart = new google.visualization.PieChart(document.getElementById('content'))
                chart.draw(json_data, options);
              }
            </script>
          </head>
          <body>
            <div id="content" style="width: 850px; height: 500px;"></div>
          </body>
        </html>
        """
