import Chart from "@/components/chart";
import { LineChart } from "echarts/charts";
import styled from "styled-components";
import NumberAnimation from "@/components/numberAnimation";
import type { TokenMap } from "../theme";
import { useDataStore } from "../stores/dataStore";
import { DC, CHART_TEXTS } from "@/config/config";

/**
 * 降级数据 — 当后端未连接或数据还没到时使用。
 * 值来自 config.ts 的 DC.chart4.defaultData。
 */
const DEFAULT_DATA = DC.chart4.defaultData;

const Wrapper = styled.div`
  width: 100%;
  height: 100%;
  display: grid;
  grid-template-columns: repeat(${DC.chart4.layout.columns}, minmax(0, 1fr));
  grid-template-rows: 2fr repeat(${DC.chart4.layout.subRows - 1}, minmax(0, 1fr));
  gap: ${DC.chart4.layout.gap}px;
`;

const Statistics = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: space-evenly;
`;

const StatisticsTitle = styled.div`
  font-size: ${DC.chart4.fonts.statisticsTitle.size}px;
  color: var(--text-secondary);
`;

const StatisticsNumber = styled(NumberAnimation)`
  display: flex;
  align-items: baseline;
  gap: 4px;
  font-size: ${DC.chart4.fonts.statisticsNumber.size}px;
  font-weight: ${DC.chart4.fonts.statisticsNumber.weight};
  color: var(--primary);

  &::after {
    content: "${CHART_TEXTS.chart4.revenueUnit}";
    display: inline-block;
    font-size: 12px;
    color: var(--text-secondary);
    font-weight: normal;
  }
`;

const Statistics1 = styled.div`
  display: flex;
  align-items: center;
  color: var(--text-secondary);
`;

const Statistics1Number = styled(NumberAnimation)`
  font-size: ${DC.chart4.fonts.statistics1Number.size}px;
  font-weight: ${DC.chart4.fonts.statistics1Number.weight};
  margin-left: 16px;
  color: var(--primary);
`;

const CompanyIcon = styled.svg.attrs({
  viewBox: "0 0 1024 1024",
  width: "1em",
  height: "1em",
  children: (
    <path d="M597.479619 154.063238V852.358095h52.150857V320.658286l169.252572 58.88a56.32 56.32 0 0 1 25.795047 42.959238l0.170667 4.388571V852.358095H902.095238V926.47619H121.904762v-74.093714h56.953905v-566.613333c0-19.456 10.166857-37.546667 26.843428-47.85981l304.444953-131.705904c38.034286-23.503238 87.332571 3.510857 87.332571 47.859809zM471.771429 482.816l-167.107048 68.266667v80.115809l167.107048-68.242286v-80.14019z m0-175.225905L304.664381 377.904762v80.530286l167.107048-70.339048v-80.457143z" />
  ),
})`
  vertical-align: middle;
  margin-right: 4px;
  fill: var(--secondary);
`;

export default function Charts4({ activeTokens }: { activeTokens: TokenMap }) {
  /**
   * 从 dataStore 读取 Chart4 数据
   *
   * 🔧 数据流：
   *   上位机 → TCP → 后端 → WebSocket → WSClient → dataStore → 这里
   *
   * 如果后端还没推送数据（chart4Data 为 null），
   * 使用 DEFAULT_DATA 作为降级值，保证页面正常显示。
   */
  const chart4Data = useDataStore((s) => s.chart4);

  // 🔧 降级策略：后端有数据用后端数据，否则用默认值
  const lineData = chart4Data?.line_data ?? DEFAULT_DATA.lineData;
  const totalRevenue = chart4Data?.total_revenue ?? DEFAULT_DATA.totalRevenue;
  const enterpriseCount = chart4Data?.enterprise_count ?? DEFAULT_DATA.enterpriseCount;

  const colors = activeTokens.chartGradient;
  return (
    <Wrapper>
      <Chart
        use={[LineChart]}
        option={{
          tooltip: {
            trigger: "axis",
            axisPointer: {
              type: "shadow",
            },
            textStyle: {
              color: activeTokens.textSecondary,
            },
            backgroundColor: activeTokens.surfaceOverlay,
            borderColor: colors[1],
            borderWidth: 1,
            borderRadius: 8,
          },
          grid: {
            top: DC.chart4.echarts.grid.top,
            bottom: DC.chart4.echarts.grid.bottom,
            left: DC.chart4.echarts.grid.left,
            right: DC.chart4.echarts.grid.right,
            outerBoundsMode: "same",
          },
          calculable: true,
          xAxis: {
            show: false,
            data: lineData,
            boundaryGap: false,
          },
          yAxis: {
            show: false,
            type: "value",
          },
          series: {
            name: "series1",
            type: "line",
            symbol: "none",
            itemStyle: {
              color: colors[0],
            },
            areaStyle: {
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: [
                  { offset: 0, color: colors[0] },
                  { offset: 1, color: "rgba(255,255,255,0.1)" },
                ],
                global: false,
              },
            },
            data: lineData,
          },
        }}
      />
      <Statistics>
        <StatisticsTitle>{CHART_TEXTS.chart4.revenueLabel}</StatisticsTitle>
        <StatisticsNumber
          value={totalRevenue}
          options={{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}
        />
      </Statistics>
      {Array.from({ length: 4 }, (_, k) => (
        <Statistics1 key={k}>
          <CompanyIcon />
          {CHART_TEXTS.chart4.enterpriseLabel}
          <Statistics1Number
            value={enterpriseCount}
            options={{ maximumFractionDigits: 0 }}
          />
        </Statistics1>
      ))}
    </Wrapper>
  );
}
