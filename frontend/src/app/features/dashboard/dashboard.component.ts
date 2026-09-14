import { Component, ChangeDetectionStrategy, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { toSignal } from '@angular/core/rxjs-interop';
import { ApiService } from '../../core/services/api.service';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatFormFieldModule, MatSelectModule, MatButtonModule, FormsModule],
  changeDetection: ChangeDetectionStrategy.Default,
  template: `
    <h1 class="mat-headline-3">Platform Metrics</h1>
    
    <div class="card-grid" *ngIf="metrics() as data">
      <mat-card>
        <mat-card-header><mat-card-title>Projects</mat-card-title></mat-card-header>
        <mat-card-content class="metric-value">{{ data.total_projects }}</mat-card-content>
      </mat-card>
      
      <mat-card>
        <mat-card-header><mat-card-title>Active Jobs</mat-card-title></mat-card-header>
        <mat-card-content class="metric-value">{{ data.active_jobs }}</mat-card-content>
      </mat-card>

      <mat-card>
        <mat-card-header><mat-card-title>Total Issues Caught</mat-card-title></mat-card-header>
        <mat-card-content class="metric-value">{{ data.total_issues_found }}</mat-card-content>
      </mat-card>
      
      <mat-card>
        <mat-card-header><mat-card-title>Avg Latency (ms)</mat-card-title></mat-card-header>
        <mat-card-content class="metric-value">{{ data.avg_latency_ms }}</mat-card-content>
      </mat-card>

      <mat-card style="border-left: 4px solid #9c27b0;">
        <mat-card-header><mat-card-title>Total Tokens Used</mat-card-title></mat-card-header>
        <mat-card-content class="metric-value">{{ data.total_tokens_used | number }}</mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
    .metric-value { font-size: 2.5rem; font-weight: 300; padding: 1rem 1rem 2rem 1rem; color: #3f51b5; }
  `]
})
export class DashboardComponent implements OnInit {
  private apiService = inject(ApiService);
  
  metrics = toSignal(this.apiService.getMetrics());

  ngOnInit() {
  }
}
