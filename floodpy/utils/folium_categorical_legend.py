def get_folium_categorical_template():
    template = """
    {% macro html(this, kwargs) %}

    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>jQuery UI Draggable - Default functionality</title>
    <link rel="stylesheet" href="//code.jquery.com/ui/1.12.1/themes/base/jquery-ui.css">

    <script src="https://code.jquery.com/jquery-1.12.4.js"></script>
    <script src="https://code.jquery.com/ui/1.12.1/jquery-ui.js"></script>

    <script>
    $( function() {
      $( "#maplegend" ).draggable({
                      start: function (event, ui) {
                          $(this).css({
                              right: "auto",
                              top: "auto",
                              bottom: "auto"
                          });
                      }
                  });
    });
    </script>
    </head>
    <body>

    <div id='maplegend' class='maplegend' 
      style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
       border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>

    <div class='legend-title'>ESA WorldCover 2021 Categories</div>
    <div class='legend-scale'>
    <ul class='legend-labels'>

      <li><span style='background:rgb(0, 0, 0); opacity:1;'></span><b>No data</b></li>
      <li><span style='background:rgb(0, 100, 0); opacity:1;'></span><b>Tree cover</b></li>
      <li><span style='background:rgb(255, 187, 34); opacity:1;'></span><b>Shrubland</b></li>
      <li><span style='background:rgb(255, 255, 76); opacity:1;'></span><b>Grassland</b></li>
      <li><span style='background:rgb(240, 150, 255); opacity:1;'></span><b>Cropland</b></li>
      <li><span style='background:rgb(250, 0, 0); opacity:1;'></span><b>Built-up</b></li>
      <li><span style='background:rgb(180, 180, 180); opacity:1;'></span><b>Bare/sparse vegetation</b></li>
      <li><span style='background:rgb(240, 240, 240); opacity:1;'></span><b>Snow and Ice</b></li>
      <li><span style='background:rgb(0, 100, 200); opacity:1;'></span><b>Permanent water bodies</b></li>
      <li><span style='background:rgb(0, 150, 160); opacity:1;'></span><b>Herbaceous wetland</b></li>
      <li><span style='background:rgb(0, 207, 117); opacity:1;'></span><b>Mangroves</b></li>
      <li><span style='background:rgb(250, 230, 160); opacity:1;'></span><b>Moss and lichen</b></li>

    </ul>
    </div>
    </div>

    </body>
    </html>

    <style type='text/css'>
    .maplegend .legend-title {
      text-align: left;
      margin-bottom: 5px;
      font-weight: bold;
      font-size: 90%;
      }
    .maplegend .legend-scale ul {
      margin: 0;
      margin-bottom: 5px;
      padding: 0;
      float: left;
      list-style: none;
      }
    .maplegend .legend-scale ul li {
      font-size: 80%;
      list-style: none;
      margin-left: 0;
      line-height: 18px;
      margin-bottom: 2px;
      }
    .maplegend ul.legend-labels li span {
      display: block;
      float: left;
      height: 16px;
      width: 30px;
      margin-right: 5px;
      margin-left: 0;
      border: 1px solid #999;
      }
    .maplegend .legend-source {
      font-size: 80%;
      color: #777;
      clear: both;
      }
    .maplegend a {
      color: #777;
      }
    </style>
    {% endmacro %}"""
    return template
