import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-sidenav',
  standalone: true,
  imports: [CommonModule, RouterModule, MatListModule, MatIconModule],
  template: `
    <mat-nav-list>
      <a mat-list-item routerLink="/dashboard" routerLinkActive="active-link">
        <mat-icon matListItemIcon>dashboard</mat-icon>
        <div matListItemTitle>Dashboard</div>
      </a>
      <a mat-list-item routerLink="/jobs" routerLinkActive="active-link">
        <mat-icon matListItemIcon>dns</mat-icon>
        <div matListItemTitle>Review Jobs</div>
      </a>
      <a mat-list-item routerLink="/integrations" routerLinkActive="active-link">
        <mat-icon matListItemIcon>integration_instructions</mat-icon>
        <div matListItemTitle>Integrations</div>
      </a>
      <a mat-list-item routerLink="/settings" routerLinkActive="active-link">
        <mat-icon matListItemIcon>settings</mat-icon>
        <div matListItemTitle>Settings</div>
      </a>
    </mat-nav-list>
  `,
  styles: [`
    .active-link { background: rgba(0, 0, 0, 0.04); border-right: 3px solid #3f51b5; }
    ::ng-deep .dark-theme .active-link { background: rgba(255, 255, 255, 0.08); border-right: 3px solid #ff4081; }
  `]
})
export class SidenavComponent {}
