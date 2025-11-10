declare module 'plotly.js-dist-min';
declare module 'react-plotly.js/factory' {
  import Plotly from 'plotly.js';
  function createPlotlyComponent(plotly: typeof Plotly): any;
  export default createPlotlyComponent;
}
