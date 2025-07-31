describe('Admin Dashboard Login Flow', () => {
  beforeEach(() => {
    
    cy.visit('/login')
  })

  it('should log in as admin and navigate to dashboard with charts loaded', () => {
    
    cy.get('[data-cy="email-input"]').type('admin@example.com')
    cy.get('[data-cy="password-input"]').type('adminpassword')
    cy.get('[data-cy="login-button"]').click()

    
    cy.url().should('not.include', '/login')
    
    
    cy.get('[data-cy="admin-nav"]').should('be.visible')
    
    
    cy.visit('/admin/dashboard')
    
    
    cy.get('[data-cy="dashboard-title"]').should('contain', 'Admin Dashboard')
    
    
    cy.get('[data-cy="books-per-club-chart"]', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.empty')
    
    cy.get('[data-cy="summaries-per-book-chart"]', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.empty')
    
    cy.get('[data-cy="active-clubs-chart"]', { timeout: 10000 })
      .should('be.visible')
      .and('not.be.empty')
    
   
    cy.get('[data-cy="books-per-club-chart"] canvas, [data-cy="books-per-club-chart"] svg')
      .should('exist')
    
    cy.get('[data-cy="summaries-per-book-chart"] canvas, [data-cy="summaries-per-book-chart"] svg')
      .should('exist')
    
    cy.get('[data-cy="active-clubs-chart"] canvas, [data-cy="active-clubs-chart"] svg')
      .should('exist')
    
    
    cy.get('[data-cy="books-per-club-chart"]')
      .find('canvas, svg')
      .should('have.attr', 'width')
      .and('not.equal', '0')
  })

  it('should not allow non-admin users to access admin dashboard', () => {
    // user
    cy.get('[data-cy="email-input"]').type('user@example.com')
    cy.get('[data-cy="password-input"]').type('userpassword')
    cy.get('[data-cy="login-button"]').click()

   
    cy.url().should('not.include', '/login')
    
    
    cy.visit('/admin/dashboard')
    
    
    cy.url().should('not.include', '/admin/dashboard')
    cy.get('body').should('contain', 'Access Denied')
      .or('contain', 'Unauthorized')
      .or('contain', '403')
  })

  it('should display admin navigation for admin users only', () => {
    // admin
    cy.get('[data-cy="email-input"]').type('admin@example.com')
    cy.get('[data-cy="password-input"]').type('adminpassword')
    cy.get('[data-cy="login-button"]').click()

    
    cy.get('[data-cy="admin-nav"]').should('be.visible')
    cy.get('[data-cy="admin-nav"]').should('contain', 'Dashboard')
    cy.get('[data-cy="admin-nav"]').should('contain', 'Users')
    cy.get('[data-cy="admin-nav"]').should('contain', 'Analytics')
  })
})
