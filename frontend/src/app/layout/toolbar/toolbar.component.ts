import { Component, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-toolbar',
  standalone: true,
  imports: [CommonModule, MatToolbarModule, MatIconModule, MatButtonModule],
  template: `
    <mat-toolbar color="primary" class="app-toolbar">
      <button mat-icon-button (click)="toggleSidenav.emit()" aria-label="Toggle sidenav">
        <mat-icon>menu</mat-icon>
      </button>
      <span class="toolbar-title">AI Developer Intelligence</span>
      <span class="spacer"></span>
      <button mat-icon-button aria-label="Notifications">
        <mat-icon>notifications</mat-icon>
      </button>
      <button mat-icon-button aria-label="User account">
        <mat-icon>account_circle</mat-icon>
      </button>
    </mat-toolbar>
  `,
  styles: [`
    .app-toolbar { position: relative; z-index: 2; box-shadow: 0 2px 4px -1px rgba(0,0,0,.2), 0 4px 5px 0 rgba(0,0,0,.14), 0 1px 10px 0 rgba(0,0,0,.12); }
    .spacer { flex: 1 1 auto; }
    .toolbar-title { font-weight: 500; letter-spacing: 0.5px; }
  `]
})
export class ToolbarComponent {
  @Output() toggleSidenav = new EventEmitter<void>();
}
