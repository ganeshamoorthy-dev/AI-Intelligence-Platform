import { Component, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-projects',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <h1 class="mat-headline-3">Webhook Configuration</h1>
    <p>To enable automatic PR reviews, you must configure a Webhook in your GitHub repository settings.</p>

    <mat-card class="webhook-card mat-elevation-z2">
      <mat-card-header>
        <mat-icon mat-card-avatar>webhook</mat-icon>
        <mat-card-title>GitHub Webhook Setup</mat-card-title>
        <mat-card-subtitle>Go to GitHub > Repository Settings > Webhooks > Add webhook</mat-card-subtitle>
      </mat-card-header>
      
      <mat-card-content>
        <div class="code-block">
          <strong>Payload URL:</strong>
          <code>https://your-domain.com/api/v1/webhooks/github</code>
        </div>
        
        <div class="code-block">
          <strong>Content type:</strong>
          <code>application/json</code>
        </div>
        
        <div class="code-block">
          <strong>Secret:</strong>
          <code>&lt;Your GitHub PAT or HMAC Secret&gt;</code>
        </div>

        <div class="code-block">
          <strong>Which events would you like to trigger this webhook?</strong>
          <p>Select "Let me select individual events" and check <strong>Pull requests</strong>.</p>
        </div>
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .webhook-card { max-width: 800px; margin-top: 1rem; }
    .code-block { margin-top: 1.5rem; }
    .code-block strong { display: block; margin-bottom: 0.5rem; color: #555; }
    code { background: #f0f0f0; padding: 0.5rem; border-radius: 4px; display: block; font-family: monospace; }
  `]
})
export class ProjectsComponent {}
