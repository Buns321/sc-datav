import Chart from "@/components/chart";
import useRafInterval from "@/hooks/useRafInterval";
import { BarChart, type BarSeriesOption } from "echarts/charts";
import {
  GridComponent,
  TooltipComponent,
  type GridComponentOption,
  type TooltipComponentOption,
} from "echarts/components";
import type { ComposeOption, EChartsType } from "echarts/core";
import { useRef } from "react";
import type { TokenMap } from "../theme";

type BarOption = ComposeOption<
  BarSeriesOption | TooltipComponentOption | GridComponentOption
>;

const data = [3000, 2000, 4000, 5000, 4500];
const xData = [
  "50万以下",
  "50～100万",
  "100～500万",
  "500～1000万",
  "1000万以上",
];
export default function Chart6({ activeTokens }: { activeTokens: TokenMap }) {
  const chartRef = useRef<EChartsType>(null);
  const tipIndex = useRef(0);
  const colors = activeTokens.chartGradient;

  useRafInterval(
    () => {
      if (chartRef.current) {
        chartRef.current?.dispatchAction({
          type: "showTip",
          seriesIndex: 0,
          dataIndex: tipIndex.current,
        });
        tipIndex.current = (tipIndex.current + 1) % data.length;
      }
    },
    3_000,
    true
  );

  return (
    <Chart<BarOption>
      ref={chartRef}
      use={[BarChart, TooltipComponent, GridComponent]}
      option={{
        tooltip: {
          trigger: "axis",
          backgroundColor: activeTokens.surfaceOverlay,
          borderColor: colors[1],
          borderWidth: 1,
          borderRadius: 8,
          textStyle: {
            color: activeTokens.textSecondary,
            fontSize: 13,
            align: "left",
          },
          axisPointer: {
            type: "line",
            lineStyle: {
              width: 1,
              type: "dotted",
              color: colors[0],
            },
          },
        },
        grid: {
          top: "20%",
          bottom: "5%",
          left: 10,
          right: 10,
          outerBoundsMode: "same",
        },
        xAxis: {
          type: "category",
          axisLine: {
            lineStyle: {
              color: activeTokens.outline,
            },
          },
          axisLabel: {
            interval: 0,
            color: activeTokens.textTertiary,
          },
          axisTick: {
            show: false,
          },
          data: xData,
        },
        yAxis: {
          type: "value",
          splitLine: {
            show: false,
          },
          axisLine: {
            show: false,
          },
          axisLabel: {
            color: activeTokens.textTertiary,
          },
          axisTick: {
            show: false,
          },
        },
        series: [
          {
            name: "",
            type: "bar",
            barWidth: 30,
            label: {
              show: true,
              position: "top",
              color: activeTokens.textSecondary,
            },
            itemStyle: {
              borderRadius: [15, 15, 0, 0],
              color: {
                type: "linear",
                x: 0,
                y: 0,
                x2: 0,
                y2: 1,
                colorStops: colors.map((color, index) => ({
                  offset: index,
                  color: color,
                })),
                global: false,
              },
            },
            data: data,
          },
        ],
      }}
    />
  );
}
