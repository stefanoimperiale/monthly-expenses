from env_variables import CURRENCY

chart_template = """
        <html>
          <head>
          <meta charset="utf-8">
            <title>Monthly Example</title>
            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
            <script type="text/javascript">
              google.charts.load('current', {'packages':['corechart']});
              google.setOnLoadCallback(drawTable);
              function drawTable() {
                var json_data = new google.visualization.arrayToDataTable(%(json)s);
                var formatter = new google.visualization.NumberFormat({prefix: '""" + CURRENCY + """ '});
                formatter.format(json_data, 1)
                var options = {
                    title: 'Monthly expenses',
                    is3D: true,
                    pieSliceText: 'label',
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
            <div id="content" style="width: 900px; height: 500px;"></div>
          </body>
        </html>
        """
