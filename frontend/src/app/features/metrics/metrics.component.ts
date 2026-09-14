import { Component, ChangeDetectionStrategy } from '@angular/core';

@Component({
  selector: 'app-metrics',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="mat-headline-3">Metrics</h1>
    <p>Average Review Time, Token Consumption, and LLM Inference Time.</p>
  `
})
export class MetricsComponent {}
